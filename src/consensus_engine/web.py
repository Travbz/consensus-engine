"""Web interface for the Consensus Engine using Gradio."""
import gradio as gr
import asyncio
import os
import socket
import logging
import signal
import sys
import inspect
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .engine import ConsensusEngine
from .models.openai import OpenAILLM
from .models.anthropic import AnthropicLLM
from .database.models import Base, Discussion

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class PortInUseError(Exception):
    """Raised when a port is already in use."""
    pass

def is_port_available(host: str, port: int) -> bool:
    """Check if a port is available on the specified host."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            return True
    except OSError:
        return False

def find_available_port(host: str, start_port: int, max_attempts: int = 100) -> int:
    """
    Find an available port starting from start_port.
    Will try ports in sequence until it finds an open one or reaches max_attempts.
    """
    for port_offset in range(max_attempts):
        port = start_port + port_offset
        if is_port_available(host, port):
            return port
    raise PortInUseError(f"Could not find an available port after {max_attempts} attempts")

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
        self.llms = [
            OpenAILLM(self.openai_key),
            AnthropicLLM(self.anthropic_key)
        ]
        self.db_session = get_db_session()
        self.engine = ConsensusEngine(self.llms, self.db_session)
        self.interface = None
        self.server_port = None
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Set up handlers for various signals."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle signals gracefully."""
        logger.info(f"\nReceived signal {signum}. Cleaning up...")
        if self.interface:
            logger.info(f"Closing Gradio interface on port {self.server_port}")
            try:
                self.interface.close()
                if self.server_port and not is_port_available("127.0.0.1", self.server_port):
                    logger.warning(f"Port {self.server_port} might still be in use")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
        
        if self.db_session:
            logger.info("Closing database session")
            self.db_session.close()
        
        logger.info("Cleanup completed")
        sys.exit(0)

    def format_timestamp(self, timestamp):
        """Format timestamp for display."""
        if timestamp:
            return timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return "N/A"

    def _get_past_discussions(self):
        """Retrieve past discussions from the database."""
        try:
            discussions = self.db_session.query(Discussion).order_by(Discussion.started_at.desc()).all()
            return [
                {
                    "id": disc.id,
                    "label": f"#{disc.id}: {disc.prompt[:50]}... ({self.format_timestamp(disc.started_at)})",
                    "prompt": disc.prompt,
                    "started_at": disc.started_at,
                    "completed_at": disc.completed_at,
                    "consensus_reached": disc.consensus_reached,
                    "final_consensus": disc.final_consensus
                }
                for disc in discussions
            ]
        except Exception as e:
            logger.error(f"Error fetching discussions: {e}")
            return []

    def _get_discussion_details(self, discussion_id):
        """Retrieve the details of a specific discussion."""
        if not discussion_id:
            return ""
        try:
            discussion = self.db_session.query(Discussion).get(discussion_id)
            if not discussion:
                return "Discussion not found."

            # Format the discussion details
            details = []
            details.append("=" * 50)
            details.append(f"Discussion #{discussion.id}")
            details.append("=" * 50)
            details.append(f"\n📅 Started: {self.format_timestamp(discussion.started_at)}")
            details.append(f"📅 Completed: {self.format_timestamp(discussion.completed_at)}")
            details.append(f"\n🎯 Original Prompt:\n{discussion.prompt}\n")
            
            # Add round details
            for round in discussion.rounds:
                details.append(f"\n📍 Round {round.round_number}:")
                for response in round.responses:
                    details.append(f"\n🤖 {response.llm_name}:\n{response.response_text}")
                details.append("-" * 40)

            # Add consensus information
            if discussion.consensus_reached:
                details.append(f"\n✅ Consensus Reached!")
                details.append(f"\n📝 Final Consensus:\n{discussion.final_consensus}")
            else:
                details.append("\n❌ No consensus reached")

            return "\n".join(details)
        except Exception as e:
            logger.error(f"Error fetching discussion details: {e}")
            return f"Error retrieving discussion details: {str(e)}"

    async def _run_discussion(self, prompt):
        """Run a discussion using the consensus engine."""
        if not prompt.strip():
            yield "Please enter a prompt to start the discussion."
            return

        try:
            yield "🚀 Starting consensus discussion...\n"
            await asyncio.sleep(0.5)  # Small delay for readability

            yield "🤖 OpenAI model thinking...\n"
            await asyncio.sleep(0.5)

            yield "🤖 Anthropic model thinking...\n"
            await asyncio.sleep(0.5)

            yield "🔄 Processing responses...\n"
            result = await self.engine.discuss(prompt)

            status = []
            if isinstance(result, dict) and "consensus" in result:
                status.extend([
                    "🎯 Discussion Complete!",
                    "🤝 Consensus Reached!\n",
                    f"📝 Final Consensus:\n{result['consensus']}\n",
                    "Individual Responses:"
                ])
                for llm_name, response in result.get("individual_responses", {}).items():
                    status.append(f"\n🤖 {llm_name}:\n{response}\n")
            else:
                status.extend([
                    "⚠️ No consensus reached. Final responses:\n"
                ])
                for k, v in result.items():
                    status.append(f"\n🤖 {k}:\n{v}\n")

            yield "\n".join(status)

        except Exception as e:
            logger.error(f"Error in run_discussion: {str(e)}", exc_info=True)
            yield f"Error running discussion: {str(e)}"

    def launch(self, host=None, port=None, debug=False):
        """Launch the Gradio interface with port retry logic."""
        host = host if host else "127.0.0.1"
        start_port = port if port else 7860
        
        try:
            actual_port = find_available_port(host, start_port)
            self.server_port = actual_port
            
            if actual_port != start_port:
                logger.info(f"Port {start_port} was in use, using port {actual_port} instead")
                print(f"Port {start_port} was in use, starting server on port {actual_port} instead")

            with gr.Blocks(title="LLM Consensus Engine") as interface:
                gr.Markdown("""
                # LLM Consensus Engine
                This tool facilitates discussions between multiple language models to reach consensus on various topics.
                """)
                
                with gr.Row():
                    with gr.Column(scale=1):
                        history_list = gr.Dropdown(
                            label="Past Discussions",
                            choices=[d["label"] for d in self._get_past_discussions()],
                            value=None,
                            interactive=True,
                            container=False
                        )
                        
                        refresh_btn = gr.Button("🔄 Refresh History", size="sm")
                    
                    with gr.Column(scale=4):
                        prompt_input = gr.Textbox(
                            label="Enter your prompt",
                            placeholder="What would you like the LLMs to discuss?",
                            lines=3
                        )
                        with gr.Row():
                            submit_btn = gr.Button("Start Discussion", variant="primary")
                            clear_btn = gr.Button("Clear", variant="secondary")

                output_box = gr.Textbox(
                    label="Discussion Output",
                    lines=25,
                    show_copy_button=True
                )

                # Event handlers
                def clear_outputs():
                    return ["", ""]
                
                def refresh_history():
                    discussions = self._get_past_discussions()
                    return gr.Dropdown(choices=[d["label"] for d in discussions])
                
                def on_history_select(selection):
                    if not selection:
                        return ""
                    discussion_id = int(selection.split(":")[0][1:])
                    return self._get_discussion_details(discussion_id)

                refresh_btn.click(
                    fn=refresh_history,
                    outputs=[history_list]
                )

                history_list.change(
                    fn=on_history_select,
                    inputs=[history_list],
                    outputs=[output_box]
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

                self.interface = interface
                
                # Launch the interface
                interface.launch(
                    server_port=actual_port,
                    share=False,
                    inbrowser=True,
                    server_name=host,
                    debug=debug
                )

        except Exception as e:
            error_msg = f"Failed to start web interface: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        finally:
            if self.db_session:
                self.db_session.close()

def main():
    """Main entry point for the web interface."""
    try:
        app = GradioInterface()
        app.launch()
    except KeyboardInterrupt:
        logger.info("\nShutdown requested... cleaning up")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()