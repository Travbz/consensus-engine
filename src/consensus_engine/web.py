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
from difflib import SequenceMatcher
from .engine import ConsensusEngine
from .models.openai import OpenAILLM
from .models.anthropic import AnthropicLLM
from .database.models import Base, Discussion, DiscussionRound
from .config.round_config import ROUND_SEQUENCE, ROUND_CONFIGS
from .config.settings import LOG_LEVEL_NUM

logging.basicConfig(level=LOG_LEVEL_NUM)
logger = logging.getLogger(__name__)

def get_db_session():
    """Initialize and return a database session."""
    database_url = os.getenv("CONSENSUS_ENGINE_DB_URL", "sqlite:///consensus_engine.db")
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def find_available_port(start_port: int, max_attempts: int = 100) -> int:
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")

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

        # Instagram-inspired colors using Gradio's theme system
        self.theme = gr.Theme.from_hub("gradio/soft")
        self.theme.font = gr.themes.GoogleFont("Inter")
        self.theme.set(
            background_fill_primary="#FFFFFF",
            background_fill_secondary="#F8F9FA",
            border_color_accent="#E4405F",
            border_color_primary="#E4E4E4",
            color_accent="#833AB4",
            button_primary_background_fill="linear-gradient(45deg, #833AB4, #E1306C)",
            button_primary_background_fill_hover="linear-gradient(45deg, #E1306C, #833AB4)",
            button_primary_text_color="#FFFFFF",
            button_secondary_background_fill="#FCAF45",
            button_secondary_background_fill_hover="#FD1D1D",
            button_secondary_text_color="#FFFFFF"
        )

    def format_timestamp(self, timestamp):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S") if timestamp else "N/A"

    def get_discussion_title(self, prompt: str) -> str:
        """Generate a readable title for a discussion."""
        if len(prompt) > 40:
            title = prompt[:40].rsplit(' ', 1)[0] + "..."
        else:
            title = prompt
        return title.strip()

    def get_discussion_history(self):
        """Get list of past discussions."""
        discussions = self.db_session.query(Discussion).order_by(desc(Discussion.started_at)).all()
        return [
            {"label": self.get_discussion_title(d.prompt), "value": str(d.id)}
            for d in discussions
        ]

    def load_discussion(self, selected):
        """Load a past discussion's details."""
        if not selected:
            return "", ""
        
        try:
            # Get discussion by ID, handling both string and dict inputs
            disc_id = selected["value"] if isinstance(selected, dict) else str(selected)
            discussion = self.db_session.query(Discussion).filter(Discussion.id == disc_id).first()
            
            if not discussion:
                return "", f"Discussion not found for ID: {disc_id}"

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
            
        except Exception as e:
            logger.error(f"Error loading discussion: {e}")
            return "", f"Error loading discussion: {str(e)}"

    async def _run_discussion(self, prompt):
        """Run a discussion using the consensus engine."""
        if not prompt.strip():
            return "Please enter a prompt to start the discussion."

        try:
            current_output = []

            def progress_callback(msg: str):
                nonlocal current_output
                
                if "Starting consensus discussion" in msg:
                    current_output.append("\n🎲 Starting new discussion...")
                    current_output.append(f"Query: {prompt}\n")
                    current_output.append("=" * 50)
                    
                elif any(round_type in msg for round_type in ROUND_SEQUENCE):
                    if "Starting" in msg:
                        round_type = next(rt for rt in ROUND_SEQUENCE if rt in msg)
                        config = ROUND_CONFIGS[round_type]
                        current_output.append(f"\n\n🎲 Round: {round_type}")
                        current_output.append(f"Stage: {config['name']}")
                        current_output.append(f"Target confidence: {config['required_confidence']:.2f}")
                        current_output.append("-" * 50)
                        current_output.append("\n[Round Progress]")
                    
                elif "Getting" in msg and "'s response" in msg:
                    llm_name = msg.split("Getting")[1].split("'s")[0].strip()
                    current_output.append(f"  > {llm_name} is thinking... 🤔")
                    
                elif "response\n" in msg and "confidence:" in msg:
                    parts = msg.split("response\n")
                    llm_name = parts[0].strip()
                    response_content = parts[1].split("\nconfidence:")[0].strip()
                    confidence = float(parts[1].split("confidence:")[1].strip())
                    
                    current_output.append(f"  > {llm_name}:")
                    current_output.append("  " + "-" * 28)
                    indented_response = "\n".join("    " + line for line in response_content.split("\n"))
                    current_output.append(indented_response)
                    current_output.append("  " + "-" * 28)
                    current_output.append(f"  Confidence: {confidence:.2f} ✓\n")

                elif "Round" in msg and "Summary" in msg:
                    current_output.append("\n[Round Summary]")
                    summary_lines = msg.split("\n")
                    for line in summary_lines:
                        if line.strip():
                            current_output.append(f"  {line.strip()}")
                    current_output.append("")
                else:
                    current_output.append(msg)

                return "\n".join(current_output)

            result = await self.engine.discuss(prompt, progress_callback)
            
            if isinstance(result, dict) and "consensus" in result:
                current_output.append("\n\n🏆 Consensus Reached!")
                current_output.append("=" * 50)
                current_output.append("\nFinal Consensus:")
                current_output.append("-" * 50)
                current_output.append(result["consensus"])
                current_output.append("\nIndividual Final Positions:")
                current_output.append("-" * 50)
                for name, response in result["individual_responses"].items():
                    current_output.append(f"\n{name}:")
                    current_output.append(response)
            else:
                current_output.append("\n\n❌ No Consensus Reached")
                current_output.append("=" * 50)
                
                # Extract and compare final positions
                positions = {}
                for name, response in result.items():
                    if "FINAL_POSITION:" in response:
                        position = response.split("FINAL_POSITION:")[1].split("IMPLEMENTATION:")[0].strip()
                        positions[name] = position

                if len(positions) >= 2:
                    similarity = SequenceMatcher(None, 
                        positions[list(positions.keys())[0]], 
                        positions[list(positions.keys())[1]]
                    ).ratio()
                    current_output.append(f"\nFinal position similarity: {similarity:.2%}")
                    current_output.append(f"Required threshold: {self.engine.consensus_threshold:.2%}")
                    if similarity >= self.engine.consensus_threshold:
                        current_output.append("\nNote: Final positions appear to agree, but full responses differ.")
                
                current_output.append("\nFinal Positions:")
                current_output.append("-" * 50)
                for name, response in result.items():
                    current_output.append(f"\n{name}:")
                    current_output.append(response)

            return "\n".join(current_output)

        except Exception as e:
            logger.error(f"Error during discussion: {e}", exc_info=True)
            return f"Error during discussion: {str(e)}"

    def create_interface(self):
        """Create the Gradio interface."""
        interface = gr.Blocks(title="LLM Consensus Engine", theme=self.theme)
        
        with interface:
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
                        value=None,
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
                label="Conference Room",
                lines=25,
                show_copy_button=True,
                interactive=False
            )

            def clear_outputs():
                return ["", ""]

            def refresh_history():
                new_choices = self.get_discussion_history()
                return gr.Dropdown(choices=new_choices)

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
            
            try:
                port = find_available_port(start_port)
                logger.info(f"Found available port: {port}")
            except RuntimeError as e:
                logger.error(f"Port finding failed: {e}")
                port = start_port  # Fall back to original port and let Gradio handle it
            
            interface = self.create_interface()
            interface.launch(
                server_port=port,
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