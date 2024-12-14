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

logger = logging.getLogger(__name__)

class ConsensusEngine:
    def __init__(self, llms: List[BaseLLM], db_session: Session):
        self.llms = llms
        self.db = db_session
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
        except:
            logger.warning("NLTK data download failed, falling back to simpler consensus check")

    def _calculate_similarity(self, responses: Dict[str, str]) -> float:
        """Calculate semantic similarity between responses using TF-IDF and cosine similarity."""
        try:
            texts = list(responses.values())
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(texts)
            similarities = cosine_similarity(tfidf_matrix)
            avg_similarity = (similarities.sum() - len(texts)) / (len(texts) * (len(texts) - 1))
            logger.debug(f"Average similarity score: {avg_similarity:.3f}")
            return avg_similarity
        except Exception as e:
            logger.warning(f"Error calculating similarity: {e}")
            return 0.0

    def _extract_key_points(self, response: str) -> str:
        """Extract main points from a response."""
        try:
            sentences = sent_tokenize(response)[:3]  # Get first three sentences
            return ' '.join(sentences)
        except Exception as e:
            logger.warning(f"Error extracting key points: {e}")
            return response[:200] + "..."  # Fallback to simple truncation

    def _identify_key_differences(self, responses: Dict[str, str]) -> str:
        """Identify main points of disagreement between responses."""
        try:
            differences = []
            for name1, response1 in responses.items():
                for name2, response2 in responses.items():
                    if name1 < name2:  # Avoid comparing same pairs twice
                        similarity = self._calculate_pairwise_similarity(response1, response2)
                        if similarity < CONSENSUS_THRESHOLD:
                            key_points1 = self._extract_key_points(response1)
                            key_points2 = self._extract_key_points(response2)
                            differences.append(f"{name1} vs {name2} (similarity: {similarity:.2f}):")
                            differences.append(f"- {name1}: {key_points1}")
                            differences.append(f"- {name2}: {key_points2}\n")
            
            return "\n".join(differences) if differences else "Models are fairly aligned but haven't reached consensus threshold."
        except Exception as e:
            logger.warning(f"Error identifying differences: {e}")
            return "Could not analyze differences in detail."

    def _calculate_pairwise_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        try:
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix)[0][1]
            return similarity
        except Exception as e:
            logger.warning(f"Error calculating pairwise similarity: {e}")
            return 0.0

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
                "Please create a unified response that captures all key points and shared understanding "
                "in a clear and concise way:\n\n"
            )
            
            for llm_name, response in responses.items():
                synthesis_prompt += f"{llm_name}:\n{response}\n\n"
            
            logger.info("Creating unified consensus response...")
            unified_response = await self.llms[0].generate_response(synthesis_prompt)
            return unified_response
            
        except Exception as e:
            logger.warning(f"Error creating unified response: {e}")
            # Fallback: Concatenate responses with headers
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
                
                # Show key differences being discussed
                differences = self._identify_key_differences(responses)
                await update_progress(f"\nMain points of discussion:\n{differences}\n")
                
                # Get new responses
                new_responses = {}
                for llm in self.llms:
                    await update_progress(f"💭 Getting {llm.name}'s thoughts on the discussion...")
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

    async def load_discussion(self, discussion_id: int) -> Optional[Dict[str, List[Dict[str, str]]]]:
        """Load a previous discussion from the database."""
        discussion = self.db.query(Discussion).get(discussion_id)
        if not discussion:
            return None
            
        result = {
            'prompt': discussion.prompt,
            'consensus_reached': bool(discussion.consensus_reached),
            'final_consensus': discussion.final_consensus,
            'rounds': []
        }
        
        for round in discussion.rounds:
            round_responses = {
                'round_number': round.round_number,
                'responses': []
            }
            for response in round.responses:
                round_responses['responses'].append({
                    'llm_name': response.llm_name,
                    'response': response.response_text
                })
            result['rounds'].append(round_responses)
            
        return result