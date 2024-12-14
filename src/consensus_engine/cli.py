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
from .web import GradioInterface
import logging

# Configure logging
logging.basicConfig(level=LOG_LEVEL_NUM)
console = Console()

def get_db_session():
    """Initialize and return a database session."""
    database_url = os.getenv("CONSENSUS_ENGINE_DB_URL", "sqlite:///consensus_engine.db")
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

async def update_display(msg: str):
    """Update the console display with new messages."""
    console.print(Panel(msg, border_style="blue"))

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

@click.command()
@click.option('--web', is_flag=True, help='Launch in web interface mode')
@click.option('--cli', is_flag=True, help='Launch in CLI mode')
@click.option('--port', default=7860, help='Port for web interface')
@click.option('--host', default="127.0.0.1", help='Host for web interface')
@click.option('--list', 'list_mode', is_flag=True, help='List past discussions')
@click.option('--view', type=int, help='View a specific discussion by ID')
@click.option('--debug', is_flag=True, help='Enable debug logging')
def main(web, cli, port, host, list_mode, view, debug):
    """Consensus Engine - Orchestrate discussions between multiple LLMs."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    db_session = get_db_session()

    try:
        if list_mode:
            list_discussions(db_session)
            return

        if view is not None:
            engine = ConsensusEngine([], db_session)
            discussion = asyncio.run(engine.load_discussion(view))
            if not discussion:
                console.print(f"[red]No discussion found with ID {view}[/red]")
                return
                
            console.print(Panel(
                discussion['prompt'],
                title="Original Prompt",
                border_style="blue"
            ))
            
            if discussion['consensus_reached']:
                console.print("\n[bold green]✅ Consensus Reached[/bold green]")
                console.print(Panel(
                    discussion['final_consensus'],
                    title="Final Consensus",
                    border_style="green"
                ))
            else:
                console.print("\n[bold yellow]❌ No Consensus Reached[/bold yellow]")

            for round in discussion['rounds']:
                console.print(f"\n[bold blue]Round {round['round_number']}:[/bold blue]")
                for response in round['responses']:
                    console.print(Panel(
                        response['response'],
                        title=response['llm_name'],
                        border_style="green"
                    ))
            return

        if web:
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

            # Initialize LLMs
            llms = [
                OpenAILLM(openai_key),
                AnthropicLLM(anthropic_key)
            ]
            
            engine = ConsensusEngine(llms, db_session)
            
            # Get prompt
            prompt = console.input("\n[bold green]Enter your prompt:[/bold green] ")
            if not prompt.strip():
                console.print("[red]Error: Prompt cannot be empty[/red]")
                return
            
            console.print("\n[bold blue]Starting consensus discussion...[/bold blue]\n")
            
            # Run discussion
            responses = asyncio.run(engine.discuss(prompt, update_display))
            
            if isinstance(responses, dict) and "consensus" in responses:
                console.print("\n[bold green]🎉 Consensus Reached![/bold green]")
                console.print(Panel(
                    responses["consensus"],
                    title="Unified Consensus Response",
                    border_style="green"
                ))
                
                console.print("\n[bold blue]Individual Contributions:[/bold blue]")
                for llm_name, response in responses["individual_responses"].items():
                    console.print(Panel(
                        response,
                        title=f"{llm_name}'s Response",
                        border_style="blue"
                    ))
            else:
                console.print("\n[bold yellow]⚠️ No Consensus Reached - Final Individual Responses:[/bold yellow]")
                for llm_name, response in responses.items():
                    console.print(Panel(
                        response,
                        title=f"{llm_name} Final Response",
                        border_style="yellow"
                    ))

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        if debug:
            import traceback
            console.print(traceback.format_exc())
    finally:
        db_session.close()

if __name__ == "__main__":
    main()