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
        
        # Analyze responses for specific content types
        has_code = any("```" in text for text in texts)
        has_evidence = any("EVIDENCE:" in text for text in texts)
        
        if has_code:
            code_blocks = [self._extract_code_blocks(text) for text in texts]
            if all(code_blocks):
                code_similarity = self._calculate_code_similarity(code_blocks)
                metrics['similarity'] = (metrics['similarity'] + code_similarity) / 2
                
                # Compare code structure
                metrics['key_differences'].extend(self._analyze_code_differences(code_blocks))
                metrics['alignment_areas'].extend(self._analyze_code_alignments(code_blocks))
        
        if has_evidence:
            evidence_similarity = self._compare_evidence(texts)
            metrics['similarity'] = (metrics['similarity'] + evidence_similarity) / 2
            
            # Analyze evidence usage
            metrics['key_alignments'].extend(self._analyze_shared_evidence(texts))
            metrics['key_differences'].extend(self._analyze_evidence_differences(texts))
        
        # Get required thresholds
        required_confidence = ROUND_CONFIGS[round_type]["required_confidence"]
        
        # Determine consensus
        consensus_reached = (metrics['similarity'] >= self.consensus_threshold and 
                            metrics['avg_confidence'] >= required_confidence)
        
        # Add remaining issues if not at consensus
        if not consensus_reached:
            metrics['remaining_issues'] = self._identify_remaining_issues(
                texts, metrics['similarity'], self.consensus_threshold
            )
        
        return {
            'consensus_reached': consensus_reached,
            'metrics': metrics
        }

    def _analyze_code_differences(self, code_blocks: List[List[str]]) -> List[str]:
        """Analyze key differences between code implementations.
        NOTE: Depends on code block format (```) in responses from RESPONSE_FORMAT"""
        differences = []
        
        if not all(code_blocks):
            return ["Incomplete code implementation"]
        
        # Compare function signatures
        signatures = [self._extract_signatures(code) for code in code_blocks[0]]
        if len(set(signatures)) > 1:
            differences.append("Different function signatures")
        
        # Compare error handling
        error_patterns = [self._analyze_error_handling(code) for code in code_blocks[0]]
        if len(set(error_patterns)) > 1:
            differences.append("Inconsistent error handling")
        
        # Compare variable naming
        var_patterns = [self._extract_variable_patterns(code) for code in code_blocks[0]]
        if len(set(var_patterns)) > 1:
            differences.append("Different variable naming patterns")
        
        return differences

    def _analyze_code_alignments(self, code_blocks: List[List[str]]) -> List[str]:
        """Analyze areas where code implementations align."""
        alignments = []
        
        if not all(code_blocks):
            return []
        
        # Check for shared patterns
        if self._has_shared_structure(code_blocks):
            alignments.append("Consistent code structure")
        
        if self._has_shared_error_handling(code_blocks):
            alignments.append("Consistent error handling")
        
        if self._has_shared_naming(code_blocks):
            alignments.append("Consistent variable naming")
        
        return alignments

    def _identify_remaining_issues(self, texts: List[str], current_similarity: float, 
                                required_similarity: float) -> List[str]:
        """Identify specific issues preventing consensus."""
        issues = []
        
        # Structure differences
        if self._has_structural_differences(texts):
            issues.append("Response structure not aligned")
        
        # Terminology differences
        term_similarity = self._calculate_terminology_similarity(texts)
        if term_similarity < 0.8:
            issues.append("Using different terminology")
        
        # Format differences
        if self._has_format_differences(texts):
            issues.append("Output format not consistent")
        
        return issues

    def _update_round_guidance(self, round_type: str, metrics: Dict[str, Any]) -> str:
        """Generate dynamic guidance based on current consensus metrics."""
        template = ROUND_CONFIGS[round_type]["consensus_guidance"]
        
        # Format guidance with current metrics
        return template.format(
            similarity=f"{metrics['similarity']:.2f}",
            consensus_threshold=f"{self.consensus_threshold:.2f}",
            avg_confidence=f"{metrics['avg_confidence']:.2f}",
            key_differences=", ".join(metrics['key_differences']),
            alignment_areas=", ".join(metrics['alignment_areas']),
            remaining_issues=", ".join(metrics['remaining_issues']),
            key_alignments=", ".join(metrics['key_alignments'])
        )

    async def discuss(
        self,
        prompt: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Conduct a complete consensus discussion."""
        discussion = Discussion(prompt=prompt)
        self.db.add(discussion)
        self.db.commit()

        def update_progress(msg: str):
            if progress_callback:
                progress_callback(msg)
            logger.info(msg)

        try:
            update_progress("Starting consensus discussion...")
            
            previous_responses = {}
            current_round = 0
            all_responses = {}

            for round_type in ROUND_SEQUENCE:
                update_progress(f"\n📍 Starting {round_type} round...")
                
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
                        update_progress(f"Getting {llm.name}'s response...")
                        
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
                        
                        # Send detailed response update including the actual response text
                        update_progress(
                            f"LLM: {llm.name}\n"
                            f"Status: Complete ✓\n"
                            f"Response:\n{response}\n"
                            f"Confidence Score: {confidence:.2f}"
                        )

                    except Exception as e:
                        logger.error(f"Error getting {llm.name} response: {e}")
                        update_progress(f"⚠️ Error with {llm.name}: {str(e)}")
                        continue

                # Calculate round consensus
                similarity = self._calculate_similarity(round_responses)
                avg_confidence = sum(r['confidence'] for r in current_responses.values()) / len(current_responses)

                # Send detailed round summary
                update_progress(
                    f"\nRound {current_round} Summary:\n"
                    f"- Round Type: {round_type}\n"
                    f"- Similarity Score: {similarity:.2f}\n"
                    f"- Average Confidence: {avg_confidence:.2f}\n"
                    f"- Required Confidence: {ROUND_CONFIGS[round_type]['required_confidence']:.2f}"
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
                        discussion.completed_at = datetime.utcnow()
                        self.db.commit()

                        return {
                            "consensus": final_consensus,
                            "individual_responses": round_responses
                        }

                current_round += 1

            discussion.completed_at = datetime.utcnow()
            self.db.commit()

            return {name: data['response'] for name, data in all_responses.items()}

        except Exception as e:
            logger.error(f"Error during discussion: {str(e)}")
            discussion.completed_at = datetime.utcnow()
            self.db.commit()
            raise