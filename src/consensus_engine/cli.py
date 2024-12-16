"""Command-line interface for the Consensus Engine."""
import asyncio
import click
import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .engine import ConsensusEngine
from .models.openai import OpenAILLM
from .models.anthropic import AnthropicLLM
from .database.models import Base, Discussion
from .config.settings import LOG_LEVEL_NUM
from .config.round_config import ROUND_SEQUENCE
from .web import GradioInterface, find_available_port
from .utils.formatting import format_discussion_output, format_showdown_response
import logging

logging.basicConfig(level=LOG_LEVEL_NUM)
console = Console()

def get_db_session():
    """Initialize and return a database session."""
    database_url = os.getenv("CONSENSUS_ENGINE_DB_URL", "sqlite:///consensus_engine.db")
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def list_discussions(db_session):
    """List all discussions from the database."""
    discussions = db_session.query(Discussion).all()
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID")
    table.add_column("Started")
    table.add_column("Status")
    table.add_column("Prompt")
    
    for disc in discussions:
        status = "✅ Consensus" if disc.consensus_reached else "❌ No Consensus"
        prompt_preview = disc.prompt[:50] + "..." if len(disc.prompt) > 50 else disc.prompt
        table.add_row(
            str(disc.id),
            disc.started_at.strftime("%Y-%m-%d %H:%M"),
            status,
            prompt_preview
        )
    
    console.print(table)

async def run_discussion(prompt: str, engine: ConsensusEngine) -> None:
    """Run a discussion with the round-based consensus engine."""
    console.print("\n[bold blue]Starting consensus discussion...[/bold blue]")
    
    def display_progress(msg: str):
        # Format the message if it's from the SHOWDOWN round
        try:
            formatted_msg = format_discussion_output(msg)
            console.print(formatted_msg)
        except Exception as e:
            console.print(f"[yellow]Warning: Display formatting error: {e}[/yellow]")
            console.print(str(msg))
    
    try:
        result = await engine.discuss(prompt, display_progress)
        
        if isinstance(result, dict) and "consensus" in result:
            console.print("\n[bold green]🎉 Consensus Reached![/bold green]")
            console.print(Panel(
                format_discussion_output(result["consensus"]),
                title="Final Consensus",
                border_style="green"
            ))
            
            console.print("\n[bold blue]Individual Contributions:[/bold blue]")
            for llm_name, response in result["individual_responses"].items():
                console.print(Panel(
                    format_discussion_output(response),
                    title=f"{llm_name}'s Response",
                    border_style="blue"
                ))
        else:
            console.print("\n[bold yellow]⚠️ No Consensus Reached - Final Positions:[/bold yellow]")
            formatted_result = format_discussion_output(result)
            console.print(Panel(
                formatted_result,
                title="Final Responses",
                border_style="yellow"
            ))

    except Exception as e:
        console.print(f"[red]Error during discussion: {str(e)}[/red]")

@click.command()
@click.option('--web', is_flag=True, help='Launch in web interface mode')
@click.option('--cli', is_flag=True, help='Launch in CLI mode')
@click.option('--port', default=7860, help='Port for web interface')
@click.option('--host', default="127.0.0.1", help='Host for web interface')
@click.option('--list', 'list_mode', is_flag=True, help='List past discussions')
@click.option('--view', type=int, help='View a specific discussion by ID')
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--load', type=int, help='Load a previous discussion by ID and continue')
@click.option('--log-level', 
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
              case_sensitive=False),
              default='WARNING',
              help='Set the logging level')
def main(web, cli, port, host, list_mode, view, debug, load, log_level):
    """Consensus Engine - Orchestrate discussions between multiple LLMs."""
    logging.getLogger().setLevel(log_level.upper())

    db_session = get_db_session()

    try:
        if list_mode:
            list_discussions(db_session)
            return

        if view is not None:
            discussion = db_session.query(Discussion).get(view)
            if not discussion:
                console.print(f"[red]No discussion found with ID {view}[/red]")
                return
                
            console.print(Panel(
                discussion.prompt,
                title="Original Prompt",
                border_style="blue"
            ))
            
            if discussion.consensus_reached:
                console.print("\n[bold green]✅ Consensus Reached[/bold green]")
                console.print(Panel(
                    discussion.final_consensus,
                    title="Final Consensus",
                    border_style="green"
                ))
            else:
                console.print("\n[bold yellow]❌ No Consensus Reached[/bold yellow]")

            for round_num in range(len(ROUND_SEQUENCE)):
                round = next((r for r in discussion.rounds if r.round_number == round_num), None)
                if round:
                    console.print(f"\n[bold blue]Round {round_num + 1} ({ROUND_SEQUENCE[round_num]}):[/bold blue]")
                    for response in round.responses:
                        console.print(Panel(
                            response.response_text,
                            title=f"{response.llm_name} (Confidence: {response.confidence_score:.2f})",
                            border_style="blue"
                        ))
            return

        if web:
            try:
                port = find_available_port(port)
                console.print(f"[green]Using port: {port}[/green]")
            except RuntimeError as e:
                console.print(f"[yellow]Warning: {str(e)}. Using default port.[/yellow]")
            
            app = GradioInterface()
            app.launch(host=host, port=port, debug=debug)
            return

        # Default to CLI mode if no other mode specified
        if not any([web, list_mode, view]):
            cli = True

        if cli:
            # Check API keys
            openai_key = os.getenv("OPENAI_API_KEY")
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            
            if not openai_key or not anthropic_key:
                console.print("[red]Error: Missing API keys[/red]")
                console.print("Please set the following environment variables:")
                console.print("  - OPENAI_API_KEY")
                console.print("  - ANTHROPIC_API_KEY")
                return

            # Initialize LLMs and engine
            llms = [
                OpenAILLM(openai_key),
                AnthropicLLM(anthropic_key)
            ]
            
            engine = ConsensusEngine(llms, db_session)
            
            # Handle loading previous discussion
            if load is not None:
                discussion = db_session.query(Discussion).get(load)
                if not discussion:
                    console.print(f"[red]No discussion found with ID {load}[/red]")
                    return
                prompt = discussion.prompt
                console.print(f"\n[bold blue]Loaded previous discussion:[/bold blue]")
                console.print(Panel(prompt, title="Original Prompt"))
            else:
                # Get prompt
                prompt = console.input("\n[bold green]Enter your prompt:[/bold green] ")
            
            if not prompt.strip():
                console.print("[red]Error: Prompt cannot be empty[/red]")
                return
            
            # Run discussion
            asyncio.run(run_discussion(prompt, engine))

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        if debug:
            import traceback
            console.print(traceback.format_exc())
    finally:
        db_session.close()

if __name__ == "__main__":
    main()
