"""Core consensus engine implementation with rounds."""
from typing import List, Dict, Optional, Callable, Awaitable, Any
import asyncio
from sqlalchemy.orm import Session
from datetime import datetime, UTC
import logging
import nltk
import os
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import SequenceMatcher

from .models.base import BaseLLM
from .database.models import Discussion, DiscussionRound, LLMResponse
from .config.settings import CONSENSUS_SETTINGS
from .config.round_config import ROUND_CONFIGS, RESPONSE_FORMAT, ROUND_SEQUENCE

logger = logging.getLogger(__name__)

class ConsensusEngine:
    def __init__(self, llms: List[BaseLLM], db_session: Session):
        self.llms = llms
        self.db = db_session
        self.nltk_enabled = self._setup_nltk()
        self.consensus_threshold = CONSENSUS_SETTINGS["consensus_threshold"]

    def _setup_nltk(self) -> bool:
        """Set up NLTK resources.
        
        Downloads and configures required NLTK components for text analysis:
        - Creates a dedicated directory for NLTK data in project's data folder
        - Downloads 'punkt' for sentence tokenization if not present
        - Downloads 'stopwords' for filtering common words if not present
        
        Returns:
            bool: True if setup successful, False if any errors occurred
        """
        try:
            # Create data directory within project instead of home folder
            nltk_data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "nltk_data")
            os.makedirs(nltk_data_dir, exist_ok=True)
            
            for resource in ['punkt', 'stopwords']:
                try:
                    nltk.data.find(f'tokenizers/{resource}')
                except LookupError:
                    nltk.download(resource, quiet=True, download_dir=nltk_data_dir)
            
            return True
        except Exception as e:
            logger.warning(f"NLTK setup failed: {e}")
            return False

    def _calculate_similarity(self, responses: Dict[str, str]) -> float:
        """Calculate semantic similarity between responses."""
        if not responses:
            return 0.0

        def extract_final_position(text: str) -> str:
            """Extract the solution section for comparison based on round format.
            Falls back to full text if no matching section found.
            
            NOTE: If RESPONSE_FORMAT in round_config.py is updated, this function must be updated
            to match the new section headers and delimiters."""
            try:
                # Check for each possible solution section in order of rounds
                if "INITIAL_POSITION:" in text:
                    position = text.split("INITIAL_POSITION:")[1].split("CONFIDENCE:")[0].strip()
                    return position
                elif "INITIAL_SOLUTION:" in text:
                    position = text.split("INITIAL_SOLUTION:")[1].split("RATIONALE:")[0].strip()
                    return position
                elif "REFINED_SOLUTION:" in text:
                    position = text.split("REFINED_SOLUTION:")[1].split("FORMAT_IMPROVEMENTS:")[0].strip()
                    return position
                elif "IMPLEMENTATION:" in text:
                    position = text.split("IMPLEMENTATION:")[1].split("CONFIDENCE:")[0].strip()
                    return position
                return text  # Fall back to full text if no sections found
            except Exception:
                return text

        # For final round, compare only FINAL_POSITION sections
        final_round = any("FINAL_POSITION:" in resp for resp in responses.values())
        if final_round:
            texts = [extract_final_position(resp) for resp in responses.values()]
        else:
            texts = list(responses.values())
            
        cleaned_texts = [text.lower().strip() for text in texts]
        
        try:
            vectorizer = TfidfVectorizer(
                stop_words='english' if self.nltk_enabled else None,
                max_features=1000
            )
            
            tfidf_matrix = vectorizer.fit_transform(cleaned_texts)
            similarities = cosine_similarity(tfidf_matrix)
            return float(similarities.sum() - len(texts)) / (len(texts) * (len(texts) - 1)) if len(texts) > 1 else 1.0
            
        except Exception as e:
            logger.warning(f"Error in vectorization: {e}")
            # Fallback to simpler comparison
            if final_round:
                return SequenceMatcher(None, cleaned_texts[0], cleaned_texts[1]).ratio()
            else:
                common_words = set.intersection(*[set(text.split()) for text in cleaned_texts])
                total_words = max(len(set.union(*[set(text.split()) for text in cleaned_texts])), 1)
                return len(common_words) / total_words

    def _extract_confidence(self, text: str) -> float:
        """Extract confidence score from response.
        NOTE: Depends on CONFIDENCE section in RESPONSE_FORMAT from round_config.py"""
        try:
            import re
            confidence_line = re.search(r"CONFIDENCE:\s*(\d*\.?\d+)", text, re.IGNORECASE)
            if confidence_line:
                confidence = float(confidence_line.group(1))
                return confidence / 100 if confidence > 1 else confidence
        except Exception as e:
            logger.warning(f"Error extracting confidence: {e}")
        return 0.0

    def _check_consensus(self, responses: Dict[str, Dict[str, Any]], round_type: str) -> Dict[str, Any]:
        """Enhanced consensus checking with detailed feedback."""
        # Get responses and confidence scores
        texts = [data['response'] for data in responses.values()]
        confidences = [data['confidence'] for data in responses.values()]
        
        # Initialize metrics
        metrics = {
            'similarity': 0.0,
            'avg_confidence': 0.0,
            'key_differences': [],
            'alignment_areas': [],
            'remaining_issues': [],
            'key_alignments': []
        }
        
        # Calculate base similarity
        metrics['similarity'] = self._calculate_similarity({str(i): text for i, text in enumerate(texts)})
        metrics['avg_confidence'] = sum(confidences) / len(confidences)
        
        # Get required thresholds
        required_confidence = ROUND_CONFIGS[round_type]["required_confidence"]
        
        # Determine consensus
        consensus_reached = (metrics['similarity'] >= self.consensus_threshold and 
                            metrics['avg_confidence'] >= required_confidence)
        
        return {
            'consensus_reached': consensus_reached,
            'metrics': metrics
        }

    async def update_progress(self, msg: str, progress_callback: Optional[Callable[[str], Awaitable[None]]] = None):
        """Send progress update through callback if provided."""
        if progress_callback:
            if asyncio.iscoroutinefunction(progress_callback):
                await progress_callback(msg)
            else:
                progress_callback(msg)
        logger.info(msg)

    async def discuss(
        self,
        prompt: str,
        progress_callback: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """Conduct a complete consensus discussion."""
        discussion = Discussion(prompt=prompt)
        self.db.add(discussion)
        self.db.commit()

        try:
            await self.update_progress("Starting consensus discussion...", progress_callback)
            
            previous_responses = {}
            current_round = 0
            all_responses = {}

            for round_type in ROUND_SEQUENCE:
                await self.update_progress(f"\n📍 Starting {round_type} round...", progress_callback)
                
                discussion_round = DiscussionRound(
                    discussion_id=discussion.id,
                    round_number=current_round
                )
                self.db.add(discussion_round)
                self.db.commit()

                round_responses = {}
                current_responses = {}

                for llm in self.llms:
                    try:
                        await self.update_progress(f"Getting {llm.name}'s response...", progress_callback)
                        
                        full_prompt = f"""Original prompt: {prompt}\n\n"""
                        if previous_responses:
                            full_prompt += "Previous responses:\n"
                            for name, resp in previous_responses.items():
                                full_prompt += f"\n{name}: {resp}\n"
                        full_prompt += f"\n{RESPONSE_FORMAT[round_type]}"

                        response = await llm.generate_response(full_prompt)
                        confidence = self._extract_confidence(response)

                        llm_response = LLMResponse(
                            round_id=discussion_round.id,
                            llm_name=llm.name,
                            response_text=response,
                            confidence_score=confidence
                        )
                        self.db.add(llm_response)
                        self.db.commit()

                        round_responses[llm.name] = response
                        current_responses[llm.name] = {
                            'response': response,
                            'confidence': confidence
                        }
                        
                        # Send detailed response update
                        await self.update_progress(
                            f"LLM: {llm.name}\n"
                            f"Status: Complete ✓\n"
                            f"Response:\n{response}\n"
                            f"Confidence Score: {confidence:.2f}",
                            progress_callback
                        )

                    except Exception as e:
                        logger.error(f"Error getting {llm.name} response: {e}")
                        await self.update_progress(f"⚠️ Error with {llm.name}: {str(e)}", progress_callback)
                        continue

                # Calculate round consensus
                similarity = self._calculate_similarity(round_responses)
                avg_confidence = sum(r['confidence'] for r in current_responses.values()) / len(current_responses)

                # Send detailed round summary
                await self.update_progress(
                    f"\nRound {current_round} Summary:\n"
                    f"- Round Type: {round_type}\n"
                    f"- Similarity Score: {similarity:.2f}\n"
                    f"- Average Confidence: {avg_confidence:.2f}\n"
                    f"- Required Confidence: {ROUND_CONFIGS[round_type]['required_confidence']:.2f}",
                    progress_callback
                )

                # Store for next round
                previous_responses = round_responses
                all_responses = current_responses

                # Check if we reached consensus
                if similarity >= self.consensus_threshold and avg_confidence >= ROUND_CONFIGS[round_type]["required_confidence"]:
                    if round_type == ROUND_SEQUENCE[-1]:
                        consensus_llm = max(
                            current_responses.items(),
                            key=lambda x: x[1]['confidence']
                        )[0]
                        final_consensus = current_responses[consensus_llm]['response']
                        
                        discussion.consensus_reached = 1
                        discussion.final_consensus = final_consensus
                        discussion.completed_at = datetime.now(UTC)
                        self.db.commit()

                        return {
                            "consensus": final_consensus,
                            "individual_responses": round_responses
                        }

                current_round += 1

            discussion.completed_at = datetime.now(UTC)
            self.db.commit()

            return {name: data['response'] for name, data in all_responses.items()}

        except Exception as e:
            logger.error(f"Error during discussion: {str(e)}")
            discussion.completed_at = datetime.now(UTC)
            self.db.commit()
            raise

    def calculate_consensus(self, responses):
        # ... existing code ...
        
        result = {
            model: response for model, response in responses.items()
        }
        
        # Add consensus key to results
        result['consensus'] = {
            'text': self._determine_consensus_text(responses),
            'confidence': self._calculate_confidence(responses)
        }
        
        return result

    def _determine_consensus_text(self, responses):
        # Implement consensus text determination
        # This could be the most common response or a merged version
        return max(responses.values(), key=lambda x: x.get('confidence', 0)).get('text', '')

    def _calculate_confidence(self, responses):
        # Calculate overall confidence score
        confidences = [r.get('confidence', 0) for r in responses.values()]
        return sum(confidences) / len(confidences) if confidences else 0