from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, create_sdk_mcp_server
from typing import Dict, Any
import structlog
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.github_tools import create_pull_request, list_pull_requests
from tools.ast_analyzer import analyze_python_file
from tools.test_executor import run_tests
from subagents.hallucination_detector import HALLUCINATION_DETECTOR
from subagents.fix_generator import FIX_GENERATOR
from subagents.pr_manager import PR_MANAGER

logger = structlog.get_logger()

class CodeTestingAgent:
    """
    Main orchestrator for the Code Testing Agent.

    Coordinates subagents, manages custom tools, and executes
    comprehensive codebase audits.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        self.mcp_server = self._create_mcp_server()

    def _create_mcp_server(self):
        """Create MCP server with custom tools"""
        return create_sdk_mcp_server(
            name="code_testing_tools",
            version="1.0.0",
            tools=[
                create_pull_request,
                list_pull_requests,
                analyze_python_file,
                run_tests
            ]
        )

    def _build_system_prompt(self) -> str:
        """Build main agent system prompt with project context"""
        prompt_file = Path(__file__).parent.parent / "prompts" / "main_agent.txt"
        with open(prompt_file) as f:
            base_prompt = f.read()

        # Inject project-specific context
        project_context = f"""

PROJECT CONTEXT:
- Name: {self.config.get('project.name')}
- Root: {self.config.get('project.root_path')}
- GitHub: {self.config.get('github.owner')}/{self.config.get('github.repo')}
"""
        return base_prompt + project_context

    async def run(self, task: str):
        """Execute Code Testing Agent with given task"""
        logger.info("Starting Code Testing Agent", task=task[:100])

        options = ClaudeAgentOptions(
            system_prompt=self._build_system_prompt(),
            mcp_servers={"tools": self.mcp_server},
            allowed_tools=[
                "Read", "Write", "Edit", "Bash", "Glob", "Grep",
                "TodoWrite", "Task",
                "mcp__tools__create_pull_request",
                "mcp__tools__list_pull_requests",
                "mcp__tools__analyze_python_file",
                "mcp__tools__run_tests"
            ],
            agents={
                "hallucination_detector": HALLUCINATION_DETECTOR,
                "fix_generator": FIX_GENERATOR,
                "pr_manager": PR_MANAGER
            },
            model=self.config.get('agent.model'),
            permission_mode=self.config.get('agent.permission_mode'),
            max_turns=self.config.get('agent.max_turns'),
            cwd=self.config.get('project.root_path')
        )

        async with ClaudeSDKClient(options=options) as client:
            self.client = client

            # Send initial task
            await client.query(task)

            # Process messages
            async for message in client.receive_response():
                logger.info("message_received", type=type(message).__name__)
                # Messages are automatically handled by SDK
                # We're just logging for transparency

        logger.info("Code Testing Agent completed")
