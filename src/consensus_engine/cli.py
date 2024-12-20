"""Command-line interface for the Consensus Engine."""
import asyncio
import click
import os
import sys
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
import logging
from typing import Dict

logging.basicConfig(level=LOG_LEVEL_NUM)
logger = logging.getLogger(__name__)
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

def get_format_sections(round_format: str) -> Dict[str, str]:
    """Extract section labels from a round format string."""
    sections = {}
    for line in round_format.split('\n'):
        line = line.strip()
        if ':' in line and '[' in line:
            label = line.split(':')[0].strip()
            sections[label] = 'cyan'  # default color
    return sections


@click.command()
@click.option('--web', is_flag=True, help='Launch in web interface mode')
@click.option('--cli', is_flag=True, help='Launch in CLI mode')
@click.option('--port', default=7860, help='Port for web interface')
@click.option('--host', default="127.0.0.1", help='Host for web interface')
@click.option('--list', 'list_mode', is_flag=True, help='List past discussions')
@click.option('--view', type=int, help='View a specific discussion by ID')
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--file', type=click.Path(exists=True), help='Input file with prompt')
@click.option('--load', type=int, help='Load a previous discussion by ID and continue')
def main(web, cli, port, host, list_mode, view, debug, file, load):
    """Consensus Engine - Orchestrate discussions between multiple LLMs."""
    if debug:
        os.environ["CONSENSUS_ENGINE_LOG_LEVEL"] = "DEBUG"

    try:
        db_session = get_db_session()

        if list_mode:
            list_discussions(db_session)
            return 0

        if view is not None:
            discussion = db_session.query(Discussion).get(view)
            if not discussion:
                console.print(f"[red]No discussion found with ID {view}[/red]")
                return 1
                
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
            return 0

        if web:
            try:
                port = find_available_port(port)
                console.print(f"[green]Using port: {port}[/green]")
            except RuntimeError as e:
                console.print(f"[yellow]Warning: {str(e)}. Using default port.[/yellow]")
            
            app = GradioInterface()
            app.launch(host=host, port=port, debug=debug)
            return 0

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
                return 1

            # Initialize LLMs and engine
            llms = [
                OpenAILLM(openai_key),
                AnthropicLLM(anthropic_key)
            ]
            
            engine = ConsensusEngine(llms, db_session)
            
            # Get prompt
            if load is not None:
                discussion = db_session.query(Discussion).get(load)
                if not discussion:
                    console.print(f"[red]No discussion found with ID {load}[/red]")
                    return 1
                prompt = discussion.prompt
                console.print(f"\n[bold blue]Loaded previous discussion:[/bold blue]")
                console.print(Panel(prompt, title="Original Prompt"))
            elif file:
                try:
                    with open(file, 'r') as f:
                        prompt = f.read().strip()
                    if not prompt:
                        console.print("[red]Error: Input file is empty[/red]")
                        return 1
                except Exception as e:
                    console.print(f"[red]Error reading file: {str(e)}[/red]")
                    return 1
            else:
                # Get prompt
                prompt = console.input("\n[bold green]Enter your prompt:[/bold green] ")
            
            if not prompt.strip():
                console.print("[red]Error: Prompt cannot be empty[/red]")
                return 1

            # Echo input
            console.print(f"\nDiscussing: {prompt}\n")
            
            try:
                # Check if we're already in an event loop
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    # If no loop is running, create a new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(run_discussion(prompt, engine))
                else:
                    # If we're already in a loop, just run the coroutine
                    result = asyncio.run_coroutine_threadsafe(
                        run_discussion(prompt, engine),
                        loop
                    ).result()

                if not result:
                    raise click.ClickException("Discussion failed to produce a result")
                return 0
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                if debug:
                    import traceback
                    console.print(traceback.format_exc())
                raise click.ClickException(str(e))
            finally:
                if 'loop' in locals() and not loop.is_running():
                    loop.close()

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        if debug:
            import traceback
            console.print(traceback.format_exc())
        raise click.ClickException(str(e))
    finally:
        db_session.close()

async def run_discussion(prompt: str, engine: ConsensusEngine) -> dict:
    """Run a discussion and return the result."""
    def display_progress(msg: str):
        # Check if this is a round summary
        if (msg.strip().startswith('Round') and 
            'Summary:' in msg and 
            'Round Type:' in msg and 
            'Similarity Score:' in msg):
            console.print(f"[red]{msg}[/red]")
        else:
            console.print(f"[cyan]{msg}[/cyan]")

    try:
        result = await engine.discuss(prompt, display_progress)
        
        if isinstance(result, dict) and "consensus" in result:
            console.print("\n[bold green]🎉 Consensus Reached![/bold green]")
            console.print(Panel(
                result["consensus"],
                title="Final Consensus",
                border_style="green"
            ))
            
            console.print("\n[bold cyan]Individual Contributions:[/bold cyan]")
            for llm_name, response in result["individual_responses"].items():
                console.print(Panel(
                    response,
                    title=f"{llm_name}'s Response",
                    border_style="cyan"
                ))
        else:
            console.print("\n[bold yellow]⚠️ No Consensus Reached - Final Positions:[/bold yellow]")
            for llm_name, response in result.items():
                console.print(Panel(
                    response,
                    title=f"{llm_name} Final Response",
                    border_style="yellow"
                ))
                
        return result

    except Exception as e:
        console.print(f"[red]Error during discussion: {str(e)}[/red]")
        raise

if __name__ == "__main__":
    sys.exit(main())