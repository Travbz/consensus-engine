"""Core consensus engine implementation with rounds."""
from typing import List, Dict, Optional, Callable, Awaitable, Any
import asyncio
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import nltk
import os
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models.base import BaseLLM
from .database.models import Discussion, DiscussionRound, LLMResponse
from .config.settings import CONSENSUS_SETTINGS
from .config.round_config import ROUND_CONFIGS, ROUND_PROMPTS, ROUND_SEQUENCE

logger = logging.getLogger(__name__)

class ConsensusEngine:
    def __init__(self, llms: List[BaseLLM], db_session: Session):
        self.llms = llms
        self.db = db_session
        self.nltk_enabled = self._setup_nltk()
        self.consensus_threshold = CONSENSUS_SETTINGS["consensus_threshold"]

    def _setup_nltk(self) -> bool:
        """Set up NLTK resources."""
        try:
            nltk_data_dir = os.path.join(os.path.expanduser("~"), "nltk_data")
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
            common_words = set.intersection(*[set(text.split()) for text in cleaned_texts])
            total_words = max(len(set.union(*[set(text.split()) for text in cleaned_texts])), 1)
            return len(common_words) / total_words

    def _extract_confidence(self, text: str) -> float:
        try:
            import re
            confidence_line = re.search(r"CONFIDENCE:\s*(\d*\.?\d+)", text, re.IGNORECASE)
            if confidence_line:
                confidence = float(confidence_line.group(1))
                return confidence / 100 if confidence > 1 else confidence
        except Exception as e:
            logger.warning(f"Error extracting confidence: {e}")
        return 0.0

    async def discuss(
        self,
        prompt: str,
        progress_callback: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        Conduct a complete consensus discussion.
        """
        # Create new discussion
        discussion = Discussion(prompt=prompt)
        self.db.add(discussion)
        self.db.commit()

        async def update_progress(msg: str):
            if progress_callback:
                await progress_callback(msg)
            logger.info(msg)

        try:
            await update_progress("🚀 Starting consensus discussion...")
            
            previous_responses = {}
            current_round = 0
            all_responses = {}

            for round_type in ROUND_SEQUENCE:
                await update_progress(f"\n📍 Starting {round_type} round...")
                
                # Create round in database
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
                        await update_progress(f"🤖 Getting {llm.name}'s response...")
                        
                        # Construct prompt with round template
                        full_prompt = f"""Original prompt: {prompt}\n\n"""
                        if previous_responses:
                            full_prompt += "Previous responses:\n"
                            for name, resp in previous_responses.items():
                                full_prompt += f"\n{name}: {resp}\n"
                        full_prompt += f"\n{ROUND_PROMPTS[round_type]}"

                        response = await llm.generate_response(full_prompt)
                        confidence = self._extract_confidence(response)

                        # Store in database
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
                        
                        await update_progress(
                            f"\n{llm.name} response received (confidence: {confidence:.2f})"
                        )

                    except Exception as e:
                        logger.error(f"Error getting {llm.name} response: {e}")
                        await update_progress(f"⚠️ Error with {llm.name}: {str(e)}")
                        continue

                # Calculate round consensus
                similarity = self._calculate_similarity(round_responses)
                avg_confidence = sum(r['confidence'] for r in current_responses.values()) / len(current_responses)

                await update_progress(
                    f"\nRound {current_round} results:"
                    f"\nSimilarity: {similarity:.2f}"
                    f"\nAverage confidence: {avg_confidence:.2f}"
                )

                # Store for next round
                previous_responses = round_responses
                all_responses = current_responses

                # Check if we reached consensus
                if similarity >= self.consensus_threshold and avg_confidence >= ROUND_CONFIGS[round_type]["required_confidence"]:
                    # For final round, use as consensus
                    if round_type == ROUND_SEQUENCE[-1]:
                        # Use highest confidence response as consensus
                        consensus_llm = max(
                            current_responses.items(),
                            key=lambda x: x[1]['confidence']
                        )[0]
                        final_consensus = current_responses[consensus_llm]['response']
                        
                        discussion.consensus_reached = 1
                        discussion.final_consensus = final_consensus
                        discussion.completed_at = datetime.utcnow()
                        self.db.commit()

                        return {
                            "consensus": final_consensus,
                            "individual_responses": round_responses
                        }

                current_round += 1

            # If we get here, no consensus was reached
            discussion.completed_at = datetime.utcnow()
            self.db.commit()

            return {name: data['response'] for name, data in all_responses.items()}

        except Exception as e:
            logger.error(f"Error during discussion: {str(e)}")
            discussion.completed_at = datetime.utcnow()
            self.db.commit()
            raise