# """Google Gemini model implementation."""
# from typing import Dict, Optional
# import google.generativeai as genai
# import logging
# from .base import BaseLLM

# logger = logging.getLogger(__name__)

# class GeminiLLM(BaseLLM):
#     def __init__(
#         self,
#         api_key: str,
#         model: str,
#         temperature: float = 0.7,
#         max_tokens: int = 2000,
#         system_prompt: Optional[str] = None
#     ):
#         super().__init__(api_key, model, temperature, max_tokens, system_prompt)
#         genai.configure(api_key=api_key)
#         self.client = genai.GenerativeModel(model_name=self.model)
    
#     async def generate_response(self, prompt: str) -> str:
#         try:
#             response = await self.client.generate_content_async(
#                 prompt,
#                 temperature=self.temperature,
#                 max_output_tokens=self.max_tokens
#             )
#             return response.text
#         except Exception as e:
#             logger.error(f"Error generating response: {e}")
#             raise

#     async def deliberate(self, prompt: str, responses: Dict[str, str]) -> str:
#         try:
#             deliberation_prompt = (
#                 f"Original prompt: {prompt}\n\n"
#                 "Previous responses:\n"
#             )
#             for llm_name, response in responses.items():
#                 deliberation_prompt += f"\n{llm_name}: {response}\n"

#             response = await self.client.generate_content_async(
#                 deliberation_prompt,
#                 temperature=self.temperature,
#                 max_output_tokens=self.max_tokens
#             )
#             return response.text
#         except Exception as e:
#             logger.error(f"Error in deliberation: {e}")
#             raise

#     @property
#     def name(self) -> str:
#         return "Gemini"