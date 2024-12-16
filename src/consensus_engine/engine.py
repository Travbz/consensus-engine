"""Core consensus engine implementation with rounds."""
from typing import List, Dict, Optional, Callable, Any, Tuple
import asyncio
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import nltk
import os
import re
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import SequenceMatcher
from asyncio import Lock

from .models.base import BaseLLM
from .database.models import Discussion, DiscussionRound, LLMResponse
from .config.settings import CONSENSUS_SETTINGS
from .config.round_config import (
    ROUND_CONFIGS, ROUND_SEQUENCE, CONFIDENCE_GUIDANCE,
    RESPONSE_FORMAT, CODE_CONSENSUS_GUIDANCE
)

logger = logging.getLogger(__name__)

class ConsensusEngine:
    def __init__(self, llms: List[BaseLLM], db_session: Session):
        self.llms = llms
        self.db = db_session
        self.nltk_enabled = self._setup_nltk()
        self.consensus_threshold = CONSENSUS_SETTINGS["consensus_threshold"]
        self._discussion_locks = {}
        self._global_lock = Lock()

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
        """Calculate semantic similarity between responses with enhanced comparison."""
        if not responses or len(responses) < 2:
            return 0.0

        def normalize_text(text: str) -> str:
            """Normalize text for comparison."""
            # Remove code blocks for separate comparison
            text = re.sub(r'```[\s\S]*?```', '', text)
            # Standardize formatting
            text = re.sub(r'\s+', ' ', text.lower().strip())
            return text

        def extract_sections(text: str) -> Dict[str, str]:
            """Extract labeled sections from responses."""
            sections = {}
            current_section = None
            lines = []
            
            for line in text.split('\n'):
                if ':' in line and line.split(':')[0].isupper():
                    if current_section and lines:
                        sections[current_section] = ' '.join(lines)
                    current_section = line.split(':')[0]
                    lines = [line.split(':', 1)[1].strip()]
                elif current_section:
                    lines.append(line.strip())
            
            if current_section and lines:
                sections[current_section] = ' '.join(lines)
            
            return sections

        try:
            # Calculate section-by-section similarity
            section_similarities = []
            response_sections = [extract_sections(resp) for resp in responses.values()]
            
            for section_name in set().union(*(sections.keys() for sections in response_sections)):
                section_texts = [
                    sections.get(section_name, '')
                    for sections in response_sections
                ]
                if all(section_texts):
                    vectorizer = TfidfVectorizer(
                        stop_words='english' if self.nltk_enabled else None,
                        max_features=1000
                    )
                    normalized_texts = [normalize_text(text) for text in section_texts]
                    tfidf_matrix = vectorizer.fit_transform(normalized_texts)
                    similarity = cosine_similarity(tfidf_matrix)
                    avg_similarity = (similarity.sum() - len(section_texts)) / (len(section_texts) * (len(section_texts) - 1))
                    section_similarities.append(avg_similarity)
            
            # Calculate overall similarity
            return sum(section_similarities) / len(section_similarities) if section_similarities else 0.0
            
        except Exception as e:
            logger.warning(f"Error in vectorization: {e}")
            # Fallback to simple similarity
            texts = [normalize_text(text) for text in responses.values()]
            similarities = []
            for i in range(len(texts)):
                for j in range(i + 1, len(texts)):
                    similarities.append(SequenceMatcher(None, texts[i], texts[j]).ratio())
            return sum(similarities) / len(similarities) if similarities else 0.0

    def _extract_code_blocks(self, text: str) -> List[str]:
        """Extract and normalize code blocks from response."""
        pattern = r"```[\w]*\n(.*?)```"
        code_blocks = re.findall(pattern, text, re.DOTALL)
        return [self._normalize_code(block) for block in code_blocks]

    def _normalize_code(self, code: str) -> str:
        """Normalize code for comparison."""
        # Remove comments
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        # Remove empty lines and normalize whitespace
        code = '\n'.join(line.strip() for line in code.split('\n') if line.strip())
        return code

    def _calculate_code_similarity(self, code_blocks: List[List[str]]) -> float:
        """Calculate similarity between code implementations."""
        if not code_blocks or not all(code_blocks):
            return 0.0
        
        def compare_code(code1: str, code2: str) -> float:
            # Compare core structure
            struct_similarity = SequenceMatcher(None, code1, code2).ratio()
            
            # Compare function signatures
            sig1 = self._extract_signatures(code1)
            sig2 = self._extract_signatures(code2)
            sig_similarity = SequenceMatcher(None, sig1, sig2).ratio()
            
            # Compare variable naming
            vars1 = set(re.findall(r'\b[a-zA-Z_]\w*\b', code1))
            vars2 = set(re.findall(r'\b[a-zA-Z_]\w*\b', code2))
            var_similarity = len(vars1.intersection(vars2)) / len(vars1.union(vars2)) if vars1 or vars2 else 0.0
            
            # Weighted average
            return (struct_similarity * 0.5 + sig_similarity * 0.3 + var_similarity * 0.2)

        # Compare each pair of code blocks
        similarities = []
        for i in range(len(code_blocks)):
            for j in range(i + 1, len(code_blocks)):
                for code1, code2 in zip(code_blocks[i], code_blocks[j]):
                    similarities.append(compare_code(code1, code2))
                    
        return min(similarities) if similarities else 0.0

    def _extract_signatures(self, code: str) -> str:
        """Extract function signatures from code."""
        signatures = []
        for match in re.finditer(r'def\s+\w+\s*\([^)]*\)', code):
            signatures.append(match.group())
        return ' '.join(signatures)
    
    async def _get_cross_evaluations(self, responses: Dict[str, Dict[str, Any]], round_type: str) -> Dict[str, Dict[str, float]]:
        """Have each model evaluate others' responses."""
        evaluations = {}
        for evaluator_name, evaluator_data in responses.items():
            for target_name, target_data in responses.items():
                if evaluator_name != target_name:
                    # Construct evaluation prompt
                    if "```" in target_data['response']:  # Code evaluation
                        prompt = f"""
                        Evaluate this code solution:
                        {target_data['response']}
                        
                        Rate each category from 0-1:
                        1. Correctness (0-1): How well does it solve the problem?
                        2. Efficiency (0-1): How well does it use resources?
                        3. Error Handling (0-1): How well does it handle edge cases?
                        4. Code Style (0-1): How clean and maintainable is the code?
                        5. Completeness (0-1): How complete is the implementation?
                        
                        Provide your final score as:
                        EVALUATION_SCORE: [0-1]
                        """
                    else:  # Non-code evaluation
                        prompt = f"""
                        Evaluate this response:
                        {target_data['response']}
                        
                        Consider:
                        1. Accuracy of information
                        2. Completeness of answer
                        3. Clarity of explanation
                        4. Practical usefulness
                        5. Overall quality
                        
                        Provide your evaluation as a single score:
                        EVALUATION_SCORE: [0-1]
                        """
                    
                    try:
                        evaluation_response = await self.llms[evaluator_name].generate_response(prompt)
                        score = self._extract_evaluation_score(evaluation_response)  # Using new method
                        
                        if evaluator_name not in evaluations:
                            evaluations[evaluator_name] = {}
                        evaluations[evaluator_name][target_name] = score
                        
                    except Exception as e:
                        logger.error(f"Error during cross-evaluation: {e}")
                        if evaluator_name not in evaluations:
                            evaluations[evaluator_name] = {}
                        evaluations[evaluator_name][target_name] = 0.0
        
        return evaluations

    async def _select_best_implementation(self, responses: Dict[str, Dict[str, Any]], evaluations: Dict[str, Dict[str, float]]) -> str:
        """Select best implementation based on cross-evaluations."""
        avg_scores = {}
        for target_name in responses:
            scores = [evals[target_name] for evals in evaluations.values() if target_name in evals]
            avg_scores[target_name] = sum(scores) / len(scores) if scores else 0
        
        best_implementation = max(avg_scores.items(), key=lambda x: x[1])[0]
        return responses[best_implementation]['response']

    def _validate_code_implementation(self, code: str) -> bool:
        """Validate code implementation."""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py') as f:
                f.write(code)
                f.flush()
                
                # Run static analysis
                import pylint.lint
                args = [f.name]
                lint_score = pylint.lint.Run(args, do_exit=False).linter.stats['global_note']
                
                # Run tests if provided in response
                test_pattern = r'```python\s*test.*?```'
                test_matches = re.findall(test_pattern, code, re.DOTALL)
                if test_matches:
                    test_code = test_matches[0].strip('```python').strip()
                    exec(test_code)
                    
                return lint_score >= 7.0  # Minimum quality threshold
                
        except Exception as e:
            logger.error(f"Code validation error: {e}")
            return False
    def _calculate_evidence_similarity(self, responses: List[str]) -> float:
        """Calculate similarity in evidence usage."""
        def extract_evidence(text: str) -> List[str]:
            evidence = []
            if 'EVIDENCE:' in text:
                evidence_section = text.split('EVIDENCE:')[1].split('\n')[0]
                evidence = [e.strip() for e in evidence_section.split(',')]
            return evidence
        
        all_evidence = [extract_evidence(resp) for resp in responses]
        if not all(all_evidence):
            return 0.0
            
        # Calculate Jaccard similarity between evidence sets
        similarities = []
        for i in range(len(all_evidence)):
            for j in range(i + 1, len(all_evidence)):
                set1 = set(all_evidence[i])
                set2 = set(all_evidence[j])
                similarity = len(set1.intersection(set2)) / len(set1.union(set2)) if set1 or set2 else 0.0
                similarities.append(similarity)
                
        return sum(similarities) / len(similarities) if similarities else 0.0

    def _extract_confidence(self, text: str) -> float:
        """Extract and validate confidence score."""
        try:
            confidence_line = re.search(r"CONFIDENCE:\s*(\d*\.?\d+)", text, re.IGNORECASE)
            if confidence_line:
                confidence = float(confidence_line.group(1))
                return min(max(confidence / 100 if confidence > 1 else confidence, 0.0), 1.0)
        except Exception as e:
            logger.warning(f"Error extracting confidence: {e}")
        return 0.0

    def _extract_evaluation_score(self, text: str) -> float:
        """
        Extract evaluation score from cross-evaluation responses.
        Different from confidence scores - specifically for when one model evaluates another's response.
        """
        try:
            # Look specifically for evaluation score format
            eval_match = re.search(r"EVALUATION_SCORE:\s*(\d*\.?\d+)", text, re.IGNORECASE)
            if eval_match:
                score = float(eval_match.group(1))
                return min(max(score / 100 if score > 1 else score, 0.0), 1.0)
                
            # Fallback to looking for specific category scores
            categories = {
                'correctness': r"correctness.*?(\d*\.?\d+)",
                'efficiency': r"efficiency.*?(\d*\.?\d+)",
                'error_handling': r"error handling.*?(\d*\.?\d+)",
                'code_style': r"code style.*?(\d*\.?\d+)",
                'completeness': r"completeness.*?(\d*\.?\d+)"
            }
            
            scores = []
            for pattern in categories.values():
                match = re.search(pattern, text.lower())
                if match:
                    score = float(match.group(1))
                    scores.append(min(max(score / 100 if score > 1 else score, 0.0), 1.0))
            
            return sum(scores) / len(scores) if scores else 0.0
            
        except Exception as e:
            logger.warning(f"Error extracting evaluation score: {e}")
            return 0.0

    def _check_consensus(self, responses: Dict[str, Dict[str, Any]], round_type: str) -> Dict[str, Any]:
        """Enhanced consensus checking with detailed metrics."""
        # Extract responses and confidence scores
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
        
        # Check for code or evidence-based responses
        has_code = any("```" in text for text in texts)
        has_evidence = any("EVIDENCE:" in text for text in texts)
        
        if has_code:
            code_blocks = [self._extract_code_blocks(text) for text in texts]
            if all(code_blocks):
                code_similarity = self._calculate_code_similarity(code_blocks)
                # Weight code similarity more heavily for code-based responses
                metrics['similarity'] = (metrics['similarity'] * 0.3 + code_similarity * 0.7)
        
        if has_evidence:
            evidence_similarity = self._calculate_evidence_similarity(texts)
            metrics['similarity'] = (metrics['similarity'] * 0.7 + evidence_similarity * 0.3)
        
        # Get required thresholds
        required_confidence = ROUND_CONFIGS[round_type]["required_confidence"]
        
        # Determine consensus
        consensus_reached = (metrics['similarity'] >= self.consensus_threshold and 
                           metrics['avg_confidence'] >= required_confidence)
        
        return {
            'consensus_reached': consensus_reached,
            'metrics': metrics
        }

    def _format_round_prompt(self, round_type: str, prompt: str, 
                           previous_responses: Optional[Dict[str, str]] = None,
                           consensus_metrics: Optional[Dict[str, Any]] = None) -> str:
        """Format prompt with round-specific guidance and metrics."""
        round_format = RESPONSE_FORMAT[round_type]
        round_guidance = ROUND_CONFIGS[round_type]["consensus_guidance"]
        
        # Build complete prompt
        full_prompt = f"Original prompt: {prompt}\n\n"
        
        if previous_responses:
            full_prompt += "Previous responses:\n"
            for name, resp in previous_responses.items():
                full_prompt += f"\n{name}: {resp}\n"
                
        if consensus_metrics:
            # Format guidance with current metrics
            round_guidance = round_guidance.format(
                similarity=f"{consensus_metrics['similarity']:.2f}",
                consensus_threshold=f"{self.consensus_threshold:.2f}",
                avg_confidence=f"{consensus_metrics['avg_confidence']:.2f}",
                key_differences=", ".join(consensus_metrics.get('key_differences', [])),
                alignment_areas=", ".join(consensus_metrics.get('alignment_areas', [])),
                remaining_issues=", ".join(consensus_metrics.get('remaining_issues', [])),
                key_alignments=", ".join(consensus_metrics.get('key_alignments', []))
            )
        
        full_prompt += f"\n{CONFIDENCE_GUIDANCE}\n"
        full_prompt += f"\n{round_guidance}\n"
        
        # Add code guidance if needed
        if "```" in str(previous_responses):
            full_prompt += f"\n{CODE_CONSENSUS_GUIDANCE}\n"
            
        full_prompt += f"\n{round_format}\n"
        
        return full_prompt

    async def discuss(
        self,
        prompt: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Conduct a complete consensus discussion."""
        async with self._global_lock:
            discussion = Discussion(prompt=prompt)
            self.db.add(discussion)
            self.db.commit()
            self._discussion_locks[discussion.id] = Lock()

        def update_progress(msg: str):
            """Synchronous progress update."""
            if progress_callback:
                progress_callback(msg)
            logger.info(msg)

        try:
            update_progress("Starting consensus discussion...")
            
            previous_responses = {}
            current_round = 0
            consensus_metrics = None
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
                        
                        # Format prompt with current consensus metrics
                        full_prompt = self._format_round_prompt(
                            round_type, prompt, previous_responses, consensus_metrics
                        )

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

                # Calculate consensus metrics for this round
                consensus_result = self._check_consensus(current_responses, round_type)
                consensus_metrics = consensus_result['metrics']
                
                # Generate detailed round summary
                similarity = consensus_metrics['similarity']
                avg_confidence = consensus_metrics['avg_confidence']
                required_confidence = ROUND_CONFIGS[round_type]["required_confidence"]

                update_progress(
                    f"\nRound {current_round + 1} Results:\n"
                    f"- Similarity Score: {similarity:.2f} (target: {self.consensus_threshold:.2f})\n"
                    f"- Average Confidence: {avg_confidence:.2f} (required: {required_confidence:.2f})"
                )

                # Store responses for next round
                previous_responses = round_responses
                all_responses = current_responses

                # Check if we've reached consensus
                if consensus_result['consensus_reached']:
                    if round_type == ROUND_SEQUENCE[-1]:
                        # Check for code content BEFORE getting cross-evaluations
                        has_code = any("```" in resp['response'] for resp in current_responses.values())
                        
                        update_progress("\nPerforming cross-evaluations...")
                        
                        # Get cross-evaluations with scoring context
                        evaluations = await self._get_cross_evaluations(current_responses, round_type)
                        
                        # Log evaluation scores for transparency
                        for evaluator, scores in evaluations.items():
                            for target, score in scores.items():
                                update_progress(f"{evaluator} evaluated {target}'s response: {score:.2f}")
                        
                        if has_code:
                            update_progress("\nSelecting best code implementation...")
                            consensus = await self._select_best_implementation(current_responses, evaluations)
                            
                            if not self._validate_code_implementation(consensus):
                                logger.warning("Selected implementation failed validation")
                                return {
                                    "status": "no_consensus",
                                    "reason": "Code validation failed",
                                    "individual_responses": round_responses,
                                    "metrics": consensus_metrics
                                }
                        else:
                            # For non-code responses, use highest cross-evaluation score
                            consensus_llm = max(
                                evaluations.items(),
                                key=lambda x: sum(x[1].values()) / len(x[1])
                            )[0]
                            consensus = current_responses[consensus_llm]['response']


                            
                            # Update discussion record
                            discussion.consensus_reached = 1
                            discussion.final_consensus = consensus
                            discussion.completed_at = datetime.utcnow()
                            self.db.commit()

                            update_progress("\n🎉 Consensus achieved!")

                            return {
                                "status": "consensus_reached",
                                "consensus": consensus,
                                "individual_responses": round_responses,
                                "metrics": consensus_metrics,
                                "evaluations": evaluations
                            }

                current_round += 1

            # No consensus reached after all rounds
            discussion.completed_at = datetime.utcnow()
            self.db.commit()

            update_progress("\n⚠️ No consensus reached after all rounds")

            return {
                "status": "no_consensus",
                "individual_responses": {
                    name: data['response'] 
                    for name, data in all_responses.items()
                },
                "metrics": consensus_metrics
            }

        except Exception as e:
            logger.error(f"Error during discussion: {str(e)}")
            discussion.completed_at = datetime.utcnow()
            self.db.commit()
            raise

        finally:
            # Clean up discussion lock
            async with self._global_lock:
                self._discussion_locks.pop(discussion.id, None)
 