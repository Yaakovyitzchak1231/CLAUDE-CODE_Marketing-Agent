from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, create_sdk_mcp_server
from claude_agent_sdk.types import AssistantMessage, TextBlock, ThinkingBlock, ToolUseBlock, ToolResultBlock
from typing import Dict, Any, Optional
import structlog
from pathlib import Path
import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Tools
from tools.github_tools import create_pull_request, list_pull_requests
from tools.ast_analyzer import analyze_python_file
from tools.test_executor import run_tests
from tools.sandbox_executor import run_sandbox, run_benchmark
from tools.browser_automation import browser_test, browser_screenshot
from tools.api_tester import api_test, api_test_suite, health_check

# Sub-agents (original)
from subagents.hallucination_detector import HALLUCINATION_DETECTOR
from subagents.fix_generator import FIX_GENERATOR
from subagents.pr_manager import PR_MANAGER

# Sub-agents (new)
from subagents.codebase_analyzer import CODEBASE_ANALYZER
from subagents.security_auditor import SECURITY_AUDITOR
from subagents.dependency_auditor import DEPENDENCY_AUDITOR
from subagents.performance_analyzer import PERFORMANCE_ANALYZER
from subagents.integration_tester import INTEGRATION_TESTER
from subagents.browser_tester import BROWSER_TESTER

# Human-in-the-loop
from core.human_loop import HumanInTheLoop, ApprovalType

logger = structlog.get_logger()
console = Console()

# Web streaming support
web_publisher = None

class CodeTestingAgent:
    """
    Main orchestrator for the Code Testing Agent.

    Coordinates subagents, manages custom tools, and executes
    comprehensive codebase audits with real-time web streaming.
    """

    def __init__(self, config: Dict[str, Any], enable_web_stream: bool = False):
        self.config = config
        self.client = None
        self.mcp_server = self._create_mcp_server()
        self.enable_web_stream = enable_web_stream

        # Initialize web streaming if enabled
        if self.enable_web_stream:
            global web_publisher
            try:
                from web_server import publish_event
                web_publisher = publish_event
                logger.info("Web streaming enabled")
            except ImportError:
                logger.warning("Could not import web_server module, web streaming disabled")

    def _create_mcp_server(self):
        """Create MCP server with custom tools"""
        return create_sdk_mcp_server(
            name="code_testing_tools",
            version="1.0.0",
            tools=[
                # GitHub tools
                create_pull_request,
                list_pull_requests,
                # Code analysis
                analyze_python_file,
                run_tests,
                # Sandbox execution
                run_sandbox,
                run_benchmark,
                # Browser automation
                browser_test,
                browser_screenshot,
                # API testing
                api_test,
                api_test_suite,
                health_check
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

    async def run(self, task: Optional[str] = None):
        """Execute Code Testing Agent with given task (or wait for user input if task is None)"""

        if task:
            logger.info("Starting Code Testing Agent", task=task[:100])
        else:
            logger.info("Code Testing Agent ready, waiting for user input")

        # Set agent status
        if self.enable_web_stream:
            if task:
                self._set_agent_status('running')
            else:
                self._set_agent_status('waiting_for_input')
                self._publish_web_event('system', {
                    'text': '👋 Ready! Send me your first instruction to get started.'
                })

        options = ClaudeAgentOptions(
            system_prompt=self._build_system_prompt(),
            mcp_servers={"tools": self.mcp_server},
            allowed_tools=[
                # Core tools
                "Read", "Write", "Edit", "Bash", "Glob", "Grep",
                "TodoWrite", "Task",
                # GitHub tools
                "mcp__tools__create_pull_request",
                "mcp__tools__list_pull_requests",
                # Code analysis
                "mcp__tools__analyze_python_file",
                "mcp__tools__run_tests",
                # Sandbox execution
                "mcp__tools__run_sandbox",
                "mcp__tools__run_benchmark",
                # Browser automation
                "mcp__tools__browser_test",
                "mcp__tools__browser_screenshot",
                # API testing
                "mcp__tools__api_test",
                "mcp__tools__api_test_suite",
                "mcp__tools__health_check"
            ],
            agents={
                # Original sub-agents
                "hallucination_detector": HALLUCINATION_DETECTOR,
                "fix_generator": FIX_GENERATOR,
                "pr_manager": PR_MANAGER,
                # New specialized sub-agents
                "codebase_analyzer": CODEBASE_ANALYZER,
                "security_auditor": SECURITY_AUDITOR,
                "dependency_auditor": DEPENDENCY_AUDITOR,
                "performance_analyzer": PERFORMANCE_ANALYZER,
                "integration_tester": INTEGRATION_TESTER,
                "browser_tester": BROWSER_TESTER
            },
            model=self.config.get('agent.model'),
            permission_mode=self.config.get('agent.permission_mode'),
            max_turns=self.config.get('agent.max_turns'),
            cwd=self.config.get('project.root_path')
        )

        async with ClaudeSDKClient(options=options) as client:
            self.client = client
            stopped = False

            # Continuous conversation loop for web interface
            while not stopped:
                # Get task (either provided or wait for user input)
                current_task = task
                task = None  # Clear so next iteration waits for input

                if not current_task and self.enable_web_stream:
                    logger.info("Waiting for user input from web interface...")
                    self._set_agent_status('waiting_for_input')
                    self._publish_web_event('system', {
                        'text': '👋 Ready for your next instruction!'
                    })

                    user_input = await self._wait_for_user_input_async()
                    if user_input:
                        if user_input.get('type') == 'set_directory':
                            # Handle directory change
                            new_dir = user_input.get('directory', '')
                            self.config['project']['root_path'] = new_dir
                            self._publish_web_event('system', {
                                'text': f'Directory changed to: {new_dir}'
                            })
                            continue
                        current_task = user_input.get('message', '')
                        logger.info("Received task from user", task=current_task[:100] if current_task else '')
                    else:
                        logger.warning("No user input received, continuing to wait...")
                        continue

                if not current_task:
                    if not self.enable_web_stream:
                        # Non-web mode with no task, exit
                        break
                    continue

                # Process the task
                self._set_agent_status('running')

                try:
                    await client.query(current_task)

                    # Process messages with live display
                    async for message in client.receive_response():
                        # Check for control commands
                        if self.enable_web_stream:
                            control = self._check_control_commands()
                            if control:
                                if control['command'] == 'stop':
                                    logger.info("Agent stopped by user")
                                    self._set_agent_status('stopped')
                                    stopped = True
                                    break
                                elif control['command'] == 'interrupt':
                                    logger.info("Agent interrupted by user")
                                    self._set_agent_status('interrupted')
                                    break

                        self._display_message(message)

                except Exception as e:
                    logger.error(f"Error processing task: {e}")
                    self._publish_web_event('tool-error', {
                        'text': f'Error: {str(e)}'
                    })

                # If not in web mode, exit after one task
                if not self.enable_web_stream:
                    break

        if self.enable_web_stream:
            self._set_agent_status('idle')

        logger.info("Code Testing Agent completed")

    async def _wait_for_user_input_async(self, timeout: int = 3600):
        """Wait for user input asynchronously (up to timeout seconds)"""
        import asyncio

        for _ in range(timeout):
            user_input = self._get_user_input()
            if user_input:
                return user_input
            await asyncio.sleep(1)

        return None

    async def _check_for_followup_input(self, client):
        """Check if user has sent any follow-up messages"""
        import asyncio

        # Check for user input with short timeout
        for _ in range(3):  # Check 3 times with 1 second delays
            user_input = self._get_user_input()
            if user_input:
                message = user_input.get('message', '')
                if message:
                    logger.info("Received user message", message=message[:100])
                    self._set_agent_status('running')
                    await client.query(message)
                    return
            await asyncio.sleep(1)

    def _check_control_commands(self):
        """Check for control commands from web interface"""
        if web_publisher:
            try:
                from web_server import get_control_command
                return get_control_command(timeout=0)
            except:
                pass
        return None

    def _get_user_input(self):
        """Get user input from web interface"""
        if web_publisher:
            try:
                from web_server import get_user_input
                return get_user_input(timeout=0)
            except:
                pass
        return None

    def _set_agent_status(self, status):
        """Set agent status in web interface"""
        if web_publisher:
            try:
                from web_server import set_agent_status
                set_agent_status(status)
            except:
                pass

    def _display_message(self, message):
        """Display message content in real-time with rich formatting and web streaming"""
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    # Agent's thoughts and responses
                    console.print()
                    console.print(Panel(
                        Markdown(block.text),
                        title="[bold cyan]🤖 Agent Thinking[/bold cyan]",
                        border_style="cyan"
                    ))

                    # Publish to web stream
                    self._publish_web_event('thinking', {'text': block.text})

                elif isinstance(block, ThinkingBlock):
                    # Extended thinking (if model supports it)
                    console.print()
                    console.print(Panel(
                        block.thinking,
                        title="[bold magenta]💭 Deep Thinking[/bold magenta]",
                        border_style="magenta"
                    ))

                    # Publish to web stream
                    self._publish_web_event('deep-thinking', {'text': block.thinking})

                elif isinstance(block, ToolUseBlock):
                    # Tool being used
                    console.print()
                    tool_info = f"[bold yellow]Tool:[/bold yellow] {block.name}\n"
                    tool_info += f"[bold yellow]Input:[/bold yellow]\n{self._format_tool_input(block.input)}"
                    console.print(Panel(
                        tool_info,
                        title="[bold yellow]🔧 Using Tool[/bold yellow]",
                        border_style="yellow"
                    ))

                    # Publish to web stream
                    self._publish_web_event('tool-use', {
                        'tool': block.name,
                        'text': f"Using tool: {block.name}\n{self._format_tool_input(block.input)}"
                    })

                elif isinstance(block, ToolResultBlock):
                    # Tool result
                    console.print()
                    result_text = self._format_tool_result(block)
                    result_style = "red" if block.is_error else "green"
                    result_icon = "❌" if block.is_error else "✅"
                    console.print(Panel(
                        result_text,
                        title=f"[bold {result_style}]{result_icon} Tool Result[/bold {result_style}]",
                        border_style=result_style
                    ))

                    # Publish to web stream
                    event_type = 'tool-error' if block.is_error else 'tool-result'
                    self._publish_web_event(event_type, {'text': result_text})

    def _publish_web_event(self, event_type: str, data: Dict[str, Any]):
        """Publish event to web stream if enabled"""
        if self.enable_web_stream and web_publisher:
            try:
                web_publisher(event_type, data)
            except Exception as e:
                logger.warning(f"Failed to publish web event: {e}")

    def _format_tool_input(self, tool_input: Dict[str, Any]) -> str:
        """Format tool input for display"""
        formatted = ""
        for key, value in tool_input.items():
            if isinstance(value, str) and len(value) > 100:
                formatted += f"  {key}: {value[:100]}...\n"
            else:
                formatted += f"  {key}: {value}\n"
        return formatted

    def _format_tool_result(self, block: ToolResultBlock) -> str:
        """Format tool result for display"""
        if isinstance(block.content, str):
            # Limit length for display
            if len(block.content) > 500:
                return block.content[:500] + "\n... (truncated)"
            return block.content
        elif isinstance(block.content, list):
            # Handle structured content
            result = ""
            for item in block.content[:5]:  # Limit to first 5 items
                if isinstance(item, dict) and item.get('type') == 'text':
                    text = item.get('text', '')
                    if len(text) > 300:
                        result += text[:300] + "...\n"
                    else:
                        result += text + "\n"
            if len(block.content) > 5:
                result += f"\n... and {len(block.content) - 5} more items"
            return result
        return str(block.content)
