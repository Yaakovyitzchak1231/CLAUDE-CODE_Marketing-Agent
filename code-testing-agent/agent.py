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
    args = parser.parse_args()

    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        console.print(f"[red]✗ Config file not found: {config_path}[/red]")
        console.print(f"[yellow]Available configs in configs/:[/yellow]")
        for conf in Path("configs").glob("*.yaml"):
            console.print(f"  - {conf}")
        sys.exit(1)

    config = Config(args.config)

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

    # Default task
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

    console.print("[cyan]Starting audit...[/cyan]\n")

    # Run agent
    agent = CodeTestingAgent(config.config)

    try:
        await agent.run(task)
        console.print("\n[green]✓ Agent execution complete![/green]")
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Agent interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        logger.exception("agent_error")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
