from claude_agent_sdk import tool
from typing import Any, Dict
import subprocess
import time

@tool(
    "run_tests",
    "Execute test command and capture results",
    {"command": str, "timeout": int, "cwd": str}
)
async def run_tests(args: Dict[str, Any]) -> Dict[str, Any]:
    """Run test command and capture stdout, stderr, exit code"""
    try:
        start_time = time.time()

        result = subprocess.run(
            args["command"],
            shell=True,
            cwd=args.get("cwd", "."),
            timeout=args.get("timeout", 300),
            capture_output=True,
            text=True
        )

        duration = time.time() - start_time

        output_text = f"Command: {args['command']}\n"
        output_text += f"Exit Code: {result.returncode}\n"
        output_text += f"Duration: {duration:.2f}s\n\n"

        if result.returncode == 0:
            output_text += "✓ Tests PASSED\n\n"
        else:
            output_text += "✗ Tests FAILED\n\n"

        output_text += f"STDOUT:\n{result.stdout}\n\n"
        if result.stderr:
            output_text += f"STDERR:\n{result.stderr}"

        return {
            "content": [{
                "type": "text",
                "text": output_text
            }],
            "is_error": result.returncode != 0
        }
    except subprocess.TimeoutExpired:
        return {
            "content": [{
                "type": "text",
                "text": f"Test command timed out after {args.get('timeout', 300)}s"
            }],
            "is_error": True
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error running tests: {str(e)}"
            }],
            "is_error": True
        }
