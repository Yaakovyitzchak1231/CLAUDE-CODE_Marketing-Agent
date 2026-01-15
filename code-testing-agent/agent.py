#!/usr/bin/env python3
"""
Code Testing Agent - Main Entry Point

A sophisticated Claude Agent SDK application for auditing codebases,
testing for issues (including AI hallucinations), creating fixes, and
automatically submitting GitHub PRs.
"""
import asyncio
import sys
import os
from pathlib import Path
import argparse
import structlog
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from config import Config
from core.main_agent import CodeTestingAgent

console = Console()
logger = structlog.get_logger()

def setup_logging():
    """Configure structured logging"""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.dev.ConsoleRenderer()
        ]
    )

async def main():
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Code Testing Agent - Audit codebases and create fixes"
    )
    parser.add_argument(
        "--config",
        default="configs/default.yaml",
        help="Path to configuration file (default: configs/default.yaml)"
    )
    parser.add_argument(
        "--task",
        help="Specific task description (optional, uses default audit task if not provided)"
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Enable web-based streaming interface (access at http://localhost:5000)"
    )
    parser.add_argument(
        "--web-port",
        type=int,
        default=5000,
        help="Port for web interface (default: 5000)"
    )
    parser.add_argument(
        "--directory", "-d",
        help="Target directory to analyze (overrides config project.root_path)"
    )
    args = parser.parse_args()

    # Handle directory override
    if args.directory:
        target_dir = Path(args.directory).resolve()
        if not target_dir.exists():
            console.print(f"[red]Directory not found: {args.directory}[/red]")
            sys.exit(1)
        if not target_dir.is_dir():
            console.print(f"[red]Not a directory: {args.directory}[/red]")
            sys.exit(1)
        console.print(f"[cyan]Target directory: {target_dir}[/cyan]")

    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        console.print(f"[red]✗ Config file not found: {config_path}[/red]")
        console.print(f"[yellow]Available configs in configs/:[/yellow]")
        for conf in Path("configs").glob("*.yaml"):
            console.print(f"  - {conf}")
        sys.exit(1)

    config = Config(args.config)

    # Override project root if --directory was specified
    if args.directory:
        target_dir = Path(args.directory).resolve()
        config.config['project']['root_path'] = str(target_dir)
        # Try to extract project name from directory
        config.config['project']['name'] = target_dir.name

    # Display banner
    console.print(Panel.fit(
        "[bold cyan]Code Testing Agent[/bold cyan]\n" +
        f"Config: {args.config}\n" +
        f"Project: {config.get('project.name')}\n" +
        f"Model: {config.get('agent.model')}",
        border_style="cyan"
    ))

    # Check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red]✗ ANTHROPIC_API_KEY not set in environment[/red]")
        console.print("Set it with: export ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)

    # Check GitHub token
    if not os.environ.get("GITHUB_TOKEN"):
        console.print("[yellow]⚠ Warning: GITHUB_TOKEN not set. PR creation will fail.[/yellow]")
        console.print("Set it with: export GITHUB_TOKEN=your_token_here")
        console.print()

    # Start web server if enabled
    web_thread = None
    if args.web:
        import threading
        from web_server import run_server

        console.print(f"[cyan]Starting web interface at http://localhost:{args.web_port}[/cyan]")
        console.print(f"[cyan]Open your browser to see the live stream![/cyan]\n")

        web_thread = threading.Thread(
            target=run_server,
            args=('0.0.0.0', args.web_port),
            daemon=True
        )
        web_thread.start()

        # Give the server a moment to start
        await asyncio.sleep(1)

    # Determine task
    if args.web and not args.task:
        # In web mode without explicit task, wait for user input
        task = None
        console.print("[cyan]Agent ready and waiting for your instructions...[/cyan]")
        console.print(f"[cyan]Open http://localhost:{args.web_port} and send your first message![/cyan]\n")
    else:
        # Use provided task or default audit task
        task = args.task or """
        Execute a comprehensive audit of this codebase:

        1. Map the entire project structure using Glob to find all files
        2. Identify all AI/LLM integration points (search for: openai, anthropic, ollama)
        3. Test for hallucinations in AI outputs by delegating to hallucination_detector
        4. For any issues found, delegate to fix_generator to create fixes
        5. For each fix, delegate to pr_manager to submit GitHub PRs

        Be thorough and examine EVERY file systematically.
        Use TodoWrite to track your progress.
        """
        console.print("[cyan]Starting with default task...[/cyan]\n")

    # Run agent with web streaming enabled if --web flag is set
    agent = CodeTestingAgent(config.config, enable_web_stream=args.web)

    try:
        await agent.run(task)
        console.print("\n[green]✓ Agent execution complete![/green]")

        if args.web:
            console.print(f"\n[cyan]Web interface still available at http://localhost:{args.web_port}[/cyan]")
            console.print("[yellow]Press Ctrl+C to exit[/yellow]")
            # Keep the program alive so web interface stays accessible
            await asyncio.Event().wait()

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Agent interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        logger.exception("agent_error")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
