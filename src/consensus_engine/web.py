"""Web interface for the Consensus Engine using Gradio."""
import gradio as gr
import asyncio
import os
import socket
import logging
import signal
import sys
from datetime import datetime
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from .engine import ConsensusEngine
from .models.openai import OpenAILLM
from .models.anthropic import AnthropicLLM
from .database.models import Base, Discussion, DiscussionRound
from .config.round_config import ROUND_SEQUENCE

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def get_db_session():
    """Initialize and return a database session."""
    database_url = os.getenv("CONSENSUS_ENGINE_DB_URL", "sqlite:///consensus_engine.db")
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

class GradioInterface:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.openai_key or not self.anthropic_key:
            raise ValueError("Missing API keys. Please set OPENAI_API_KEY and ANTHROPIC_API_KEY environment variables.")
        
        self.llms = [
            OpenAILLM(self.openai_key),
            AnthropicLLM(self.anthropic_key)
        ]
        self.db_session = get_db_session()
        self.engine = ConsensusEngine(self.llms, self.db_session)

    def format_timestamp(self, timestamp):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S") if timestamp else "N/A"

    def get_discussion_history(self):
        """Get list of past discussions."""
        discussions = self.db_session.query(Discussion).order_by(desc(Discussion.started_at)).all()
        return [
            {
                "label": f"[{self.format_timestamp(d.started_at)}] {d.prompt[:50]}...",
                "value": d.id
            }
            for d in discussions
        ]

    def load_discussion(self, discussion_id):
        """Load a past discussion's details."""
        if not discussion_id:
            return "", ""
        
        discussion = self.db_session.query(Discussion).get(discussion_id)
        if not discussion:
            return "", "Discussion not found."

        output = []
        output.append(f"Original Prompt: {discussion.prompt}\n")
        output.append(f"Started: {self.format_timestamp(discussion.started_at)}")
        output.append(f"Status: {'Consensus Reached' if discussion.consensus_reached else 'No Consensus'}\n")

        for round in discussion.rounds:
            round_type = ROUND_SEQUENCE[round.round_number]
            output.append(f"\n=== Round {round.round_number + 1}: {round_type} ===")
            for response in round.responses:
                output.append(f"\n🤖 {response.llm_name} (Confidence: {response.confidence_score:.2f}):")
                output.append(response.response_text)
                output.append("-" * 40)

        if discussion.consensus_reached and discussion.final_consensus:
            output.append("\n✨ Final Consensus:")
            output.append(discussion.final_consensus)

        return discussion.prompt, "\n".join(output)

    async def _run_discussion(self, prompt):
        """Run a discussion using the consensus engine."""
        if not prompt.strip():
            return "Please enter a prompt to start the discussion."

        try:
            round_count = 0
            current_output = []

            async def progress_callback(msg: str):
                nonlocal round_count
                if "Starting" in msg and any(round_type in msg for round_type in ROUND_SEQUENCE):
                    round_count += 1
                    round_type = next(rt for rt in ROUND_SEQUENCE if rt in msg)
                    current_output.append(f"\n🎲 Round {round_count}: {round_type}")
                    current_output.append("=" * 40)
                elif "Getting" in msg and "'s response" in msg:
                    current_output.append(f"\n🎯 {msg}")  # "Betting" indicator
                yield "\n".join(current_output)

            result = await self.engine.discuss(prompt, progress_callback)
            
            if isinstance(result, dict) and "consensus" in result:
                current_output.append("\n🏆 Consensus Reached!\n")
                current_output.append("Final Consensus:")
                current_output.append("-" * 40)
                current_output.append(result["consensus"])
                current_output.append("\nIndividual Final Positions:")
                current_output.append("-" * 40)
                for name, response in result["individual_responses"].items():
                    current_output.append(f"\n{name}:")
                    current_output.append(response)
            else:
                current_output.append("\n❌ No Consensus Reached\n")
                current_output.append("Final Positions:")
                current_output.append("-" * 40)
                for name, response in result.items():
                    current_output.append(f"\n{name}:")
                    current_output.append(response)

            return "\n".join(current_output)

        except Exception as e:
            logger.error(f"Error during discussion: {e}", exc_info=True)
            return f"Error during discussion: {str(e)}"

    def create_interface(self):
        """Create the Gradio interface."""
        with gr.Blocks(title="LLM Consensus Engine") as interface:
            gr.Markdown("""
            # LLM Consensus Engine
            Facilitating structured discussions between multiple language models.
            """)
            
            with gr.Row():
                # Left column for history
                with gr.Column(scale=1):
                    history_dropdown = gr.Dropdown(
                        label="Previous Discussions",
                        choices=self.get_discussion_history(),
                        interactive=True,
                        container=False
                    )
                    refresh_btn = gr.Button("🔄 Refresh History", size="sm")

                # Right column for main content
                with gr.Column(scale=3):
                    prompt_input = gr.Textbox(
                        label="Enter your prompt",
                        placeholder="What would you like the LLMs to discuss?",
                        lines=3
                    )
                    with gr.Row():
                        submit_btn = gr.Button("Start Discussion", variant="primary")
                        clear_btn = gr.Button("Clear", variant="secondary")

            output_box = gr.Textbox(
                label="Discussion Progress",
                lines=25,
                show_copy_button=True
            )

            def clear_outputs():
                return ["", ""]

            def refresh_history():
                return gr.Dropdown(choices=self.get_discussion_history())

            # Event handlers
            history_dropdown.change(
                fn=self.load_discussion,
                inputs=[history_dropdown],
                outputs=[prompt_input, output_box]
            )

            refresh_btn.click(
                fn=refresh_history,
                outputs=[history_dropdown]
            )

            submit_btn.click(
                fn=self._run_discussion,
                inputs=[prompt_input],
                outputs=[output_box]
            )

            clear_btn.click(
                fn=clear_outputs,
                outputs=[prompt_input, output_box]
            )

            return interface

    def launch(self, host=None, port=None, debug=False):
        """Launch the Gradio interface."""
        try:
            host = host if host else "127.0.0.1"
            start_port = port if port else 7866
            
            interface = self.create_interface()
            interface.launch(
                server_port=start_port,
                server_name=host,
                debug=debug,
                show_api=False,
                share=False,
                inbrowser=True
            )

        except Exception as e:
            logger.error(f"Failed to start web interface: {e}", exc_info=True)
            raise

def main():
    """Main entry point for the web interface."""
    try:
        app = GradioInterface()
        app.launch()
    except KeyboardInterrupt:
        logger.info("\nShutdown requested... exiting")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error starting interface: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()