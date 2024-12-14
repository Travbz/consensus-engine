"""Web interface for the Consensus Engine using Gradio."""
import gradio as gr
import asyncio
import os
from .engine import ConsensusEngine
from .models.openai import OpenAILLM
from .models.anthropic import AnthropicLLM
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .database.models import Base
import logging

logger = logging.getLogger(__name__)

def get_db_session():
    database_url = os.getenv("CONSENSUS_ENGINE_DB_URL", "sqlite:///consensus_engine.db")
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

class GradioInterface:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.llms = [
            OpenAILLM(self.openai_key),
            AnthropicLLM(self.anthropic_key)
        ]
        self.db_session = None
        self.engine = None

    def _init_engine(self):
        if not self.db_session:
            self.db_session = get_db_session()
            self.engine = ConsensusEngine(self.llms, self.db_session)

    async def process_prompt(self, prompt, progress=gr.Progress()):
        self._init_engine()
        
        try:
            log_output = ""
            end_response = ""

            async def progress_callback(msg):
                nonlocal log_output
                log_output += f"{msg}\n"
                progress(0.5, desc=msg)
                return log_output

            # Render the discussion as it happens
            async def render_discussion(responses, final=False):
                dialog_text = ""
                for llm_name, response in responses.items():
                    dialog_text += f"**{llm_name}**:\n{response}\n\n"
                if final:
                    dialog_text += "\n**🎉 Final Consensus Response:**\n"
                    dialog_text += f"```markdown\n{end_response}\n```"
                return dialog_text

            responses = await self.engine.discuss(prompt, progress_callback)

            if isinstance(responses, dict) and "consensus" in responses:
                end_response = responses["consensus"]
                dialog_text = await render_discussion(responses["individual_responses"], final=True)
            else:
                dialog_text = await render_discussion(responses, final=False)

            return log_output, dialog_text
        
        except Exception as e:
            logger.error(f"Error processing prompt: {e}")
            return f"Error: {str(e)}", ""
        finally:
            if self.db_session:
                self.db_session.close()

    def launch(self, host=None, port=None, debug=False):
        if not self.openai_key or not self.anthropic_key:
            print("Please set OPENAI_API_KEY and ANTHROPIC_API_KEY environment variables")
            return

        # Attempt to increment the port if it is unavailable
        max_port_attempts = 10  # Maximum number of ports to try
        starting_port = port if port else 7860
        current_port = starting_port

        for attempt in range(max_port_attempts):
            try:
                with gr.Blocks(theme=gr.themes.Soft()) as interface:
                    with gr.Row():
                        gr.Markdown(
                            """
                            # LLM Consensus Engine
                            Watch AI models discuss and reach consensus on your prompt.
                            """
                        )

                    with gr.Row():
                        input_text = gr.Textbox(
                            placeholder="Enter your prompt here...",
                            label="Prompt",
                            lines=10,
                            scale=2
                        )

                    with gr.Row():
                        submit_btn = gr.Button("Start Discussion", variant="primary", scale=1)

                    with gr.Row():
                        with gr.Column():
                            log_output = gr.Textbox(
                                label="Discussion Progress",
                                lines=30,
                                max_lines=50,
                                show_copy_button=True,
                                interactive=False,
                                container=True,
                                scale=2
                            )
                        with gr.Column():
                            output_text = gr.Textbox(
                                label="Final Consensus",
                                lines=10,
                                max_lines=20,
                                show_copy_button=True,
                                interactive=False,
                                container=True,
                                scale=2
                            )

                    submit_btn.click(
                        fn=self.process_prompt,
                        inputs=input_text,
                        outputs=[log_output, output_text]
                    )

                    # Attempt to launch the Gradio interface
                    interface.launch(
                        server_port=current_port,
                        share=False,
                        inbrowser=True,
                        server_name=host if host else "127.0.0.1",
                        debug=debug
                    )
                    return  # Exit once successful

            except OSError as e:
                print(f"Port {current_port} is unavailable. Attempting next port...")
                current_port += 1  # Increment port and retry

        print(f"Error: Could not start the Gradio interface after {max_port_attempts} attempts.")

def main():
    app = GradioInterface()
    app.launch()

if __name__ == "__main__":
    main()