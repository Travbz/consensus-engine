"""Core consensus engine implementation."""
from typing import List, Dict, Optional, Callable, Awaitable
import asyncio
from sqlalchemy.orm import Session
from .models.base import BaseLLM
from .database.models import Discussion, DiscussionRound, LLMResponse
from datetime import datetime
import logging
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .config.settings import MAX_ITERATIONS, CONSENSUS_THRESHOLD
import os

logger = logging.getLogger(__name__)

class ConsensusEngine:
    def __init__(self, llms: List[BaseLLM], db_session: Session):
        self.llms = llms
        self.db = db_session
        self.nltk_enabled = self._setup_nltk()

    def _setup_nltk(self) -> bool:
        """Set up NLTK resources with proper error handling."""
        try:
            nltk_data_dir = os.path.join(os.path.expanduser("~"), "nltk_data")
            os.makedirs(nltk_data_dir, exist_ok=True)
            
            for resource in ['punkt', 'stopwords']:
                try:
                    nltk.data.find(f'tokenizers/{resource}')
                except LookupError:
                    logger.info(f"Downloading NLTK resource: {resource}")
                    nltk.download(resource, quiet=True, download_dir=nltk_data_dir)
            
            logger.info("NLTK setup completed successfully")
            return True
            
        except Exception as e:
            logger.warning(f"NLTK setup failed: {str(e)}. Falling back to basic text analysis.")
            return False

    def _calculate_similarity(self, responses: Dict[str, str]) -> float:
        """Calculate semantic similarity between responses."""
        try:
            if not responses:
                return 0.0
                
            texts = list(responses.values())
            cleaned_texts = [text.lower().strip() for text in texts]
            
            vectorizer = TfidfVectorizer(
                stop_words='english' if self.nltk_enabled else None,
                max_features=1000
            )
            
            try:
                tfidf_matrix = vectorizer.fit_transform(cleaned_texts)
                similarities = cosine_similarity(tfidf_matrix)
                avg_similarity = (similarities.sum() - len(texts)) / (len(texts) * (len(texts) - 1)) if len(texts) > 1 else 1.0
                return float(avg_similarity)
                
            except Exception as vec_error:
                logger.warning(f"Error in vectorization: {vec_error}. Using fallback similarity method.")
                common_words = set.intersection(*[set(text.split()) for text in cleaned_texts])
                total_words = max(len(set.union(*[set(text.split()) for text in cleaned_texts])), 1)
                return len(common_words) / total_words
                
        except Exception as e:
            logger.warning(f"Error calculating similarity: {e}")
            return 0.0

    def _extract_key_points(self, response: str) -> str:
        """Extract main points from a response."""
        try:
            if self.nltk_enabled:
                sentences = sent_tokenize(response)
                return ' '.join(sentences[:3])
            else:
                sentences = [s.strip() for s in response.split('.') if s.strip()]
                return '. '.join(sentences[:3]) + ('.' if sentences else '')
                
        except Exception as e:
            logger.warning(f"Error extracting key points: {e}")
            return response[:200] + "..."

    def _identify_key_differences(self, responses: Dict[str, str]) -> str:
        """Identify main points of disagreement between responses."""
        differences = []
        for name1, response1 in responses.items():
            for name2, response2 in responses.items():
                if name1 < name2:
                    similarity = self._calculate_similarity({name1: response1, name2: response2})
                    if similarity < CONSENSUS_THRESHOLD:
                        key_points1 = self._extract_key_points(response1)
                        key_points2 = self._extract_key_points(response2)
                        differences.append(f"{name1} vs {name2} (similarity: {similarity:.2f}):")
                        differences.append(f"- {name1}: {key_points1}")
                        differences.append(f"- {name2}: {key_points2}\n")
        
        return "\n".join(differences) if differences else "Models are fairly aligned but haven't reached consensus threshold."

    def _check_consensus(self, responses: Dict[str, str]) -> bool:
        """Check if consensus has been reached."""
        if len(responses) <= 1:
            return True
        
        similarity_score = self._calculate_similarity(responses)
        has_consensus = similarity_score >= CONSENSUS_THRESHOLD
        logger.info(f"Consensus check: similarity={similarity_score:.3f}, threshold={CONSENSUS_THRESHOLD}, reached={has_consensus}")
        return has_consensus

    async def _create_unified_response(self, responses: Dict[str, str]) -> str:
        """Create a unified response when consensus is reached."""
        try:
            synthesis_prompt = (
                "The following responses have reached consensus. "
                "Please create a unified response that captures all key points and shared understanding:\n\n"
            )
            
            for llm_name, response in responses.items():
                synthesis_prompt += f"{llm_name}:\n{response}\n\n"
            
            unified_response = await self.llms[0].generate_response(synthesis_prompt)
            return unified_response
            
        except Exception as e:
            logger.warning(f"Error creating unified response: {e}")
            unified = "Consensus Reached - Combined Responses:\n\n"
            for llm_name, response in responses.items():
                unified += f"From {llm_name}:\n{response}\n\n"
            return unified

    async def discuss(self, prompt: str, progress_callback: Optional[Callable[[str], Awaitable[None]]] = None) -> Dict[str, str]:
        """
        Conduct a consensus discussion.
        
        Args:
            prompt: The initial prompt/question
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict containing either:
            - {"consensus": str} if consensus is reached
            - {llm_name: response} for each LLM if no consensus
        """
        async def update_progress(msg: str):
            if progress_callback:
                await progress_callback(msg)
            logger.info(msg)

        # Create new discussion
        discussion = Discussion(prompt=prompt)
        self.db.add(discussion)
        self.db.commit()
        
        try:
            await update_progress("🚀 Starting consensus discussion...")
            await update_progress(f"📝 Prompt: {prompt}\n")
            
            # Get initial responses
            responses = {}
            current_round = DiscussionRound(
                discussion_id=discussion.id,
                round_number=0
            )
            self.db.add(current_round)
            self.db.commit()
            
            # Initial responses
            for llm in self.llms:
                await update_progress(f"💭 Getting response from {llm.name}...")
                response = await llm.generate_response(prompt)
                responses[llm.name] = response
                llm_response = LLMResponse(
                    round_id=current_round.id,
                    llm_name=llm.name,
                    response_text=response
                )
                self.db.add(llm_response)
                key_points = self._extract_key_points(response)
                await update_progress(f"\n{llm.name} main points:\n{key_points}\n")
            
            self.db.commit()
            
            # Deliberation rounds
            iteration = 0
            while iteration < MAX_ITERATIONS:
                similarity = self._calculate_similarity(responses)
                await update_progress(f"\n📊 Current agreement level: {similarity:.2f}")
                
                if self._check_consensus(responses):
                    await update_progress("\n🎉 Consensus reached!")
                    unified_response = await self._create_unified_response(responses)
                    
                    discussion.consensus_reached = 1
                    discussion.final_consensus = unified_response
                    discussion.completed_at = datetime.utcnow()
                    self.db.commit()
                    
                    await update_progress("\n📝 Unified Consensus Response:")
                    await update_progress(unified_response)
                    
                    return {
                        "consensus": unified_response,
                        "individual_responses": responses
                    }
                
                iteration += 1
                await update_progress(f"\n🤔 Round {iteration}/{MAX_ITERATIONS}: Models discussing differences...")
                
                current_round = DiscussionRound(
                    discussion_id=discussion.id,
                    round_number=iteration
                )
                self.db.add(current_round)
                self.db.commit()
                
                differences = self._identify_key_differences(responses)
                await update_progress(f"\nMain points of discussion:\n{differences}\n")
                
                new_responses = {}
                for llm in self.llms:
                    await update_progress(f"💭 Getting {llm.name}'s thoughts...")
                    deliberation = await llm.deliberate(prompt, responses)
                    new_responses[llm.name] = deliberation
                    llm_response = LLMResponse(
                        round_id=current_round.id,
                        llm_name=llm.name,
                        response_text=deliberation
                    )
                    self.db.add(llm_response)
                    key_points = self._extract_key_points(deliberation)
                    await update_progress(f"\n{llm.name}'s main points:\n{key_points}\n")
                
                self.db.commit()
                responses = new_responses

            await update_progress("\n⚠️ Maximum rounds reached without consensus")
            discussion.completed_at = datetime.utcnow()
            self.db.commit()
            return responses
            
        except Exception as e:
            logger.error(f"Error during discussion: {str(e)}", exc_info=True)
            discussion.completed_at = datetime.utcnow()
            self.db.commit()
            raise e