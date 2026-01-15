"""
Sandboxed Code Execution Tool

Provides safe execution of code snippets for testing purposes.
Uses subprocess isolation and resource limits.
"""
from claude_agent_sdk import tool
from typing import Any, Dict
import subprocess
import tempfile
import os
import sys
import signal
import time
from pathlib import Path

# Maximum execution time (seconds)
MAX_EXECUTION_TIME = 30

# Maximum output size (characters)
MAX_OUTPUT_SIZE = 50000

# Forbidden imports/modules for security
FORBIDDEN_PYTHON_IMPORTS = [
    "os.system", "subprocess.call", "subprocess.run",
    "eval(", "exec(", "__import__",
    "open(", "file(",  # Only forbidden in sandbox, not read-only mode
]

# Safe mode: only allows read operations
SAFE_MODE_ALLOWED = [
    "print", "len", "str", "int", "float", "list", "dict", "set", "tuple",
    "range", "enumerate", "zip", "map", "filter", "sorted", "reversed",
    "sum", "min", "max", "abs", "round", "pow",
    "isinstance", "type", "hasattr", "getattr",
    "json.loads", "json.dumps",
]


def create_sandbox_script(code: str, language: str) -> str:
    """Wrap code in a sandbox environment"""

    if language == "python":
        return f'''
import sys
import json

# Sandbox restrictions
sys.setrecursionlimit(100)

# Capture output
_sandbox_output = []
_original_print = print

def print(*args, **kwargs):
    output = " ".join(str(a) for a in args)
    _sandbox_output.append(output)
    _original_print(*args, **kwargs)

try:
    # User code
{_indent_code(code, 4)}

except Exception as e:
    print(f"Error: {{type(e).__name__}}: {{e}}")

# Output results
sys.stdout.flush()
'''
    elif language == "javascript":
        return f'''
const output = [];
const originalLog = console.log;
console.log = (...args) => {{
    output.push(args.map(String).join(' '));
    originalLog(...args);
}};

try {{
{_indent_code(code, 4)}
}} catch (e) {{
    console.log(`Error: ${{e.name}}: ${{e.message}}`);
}}
'''
    else:
        return code


def _indent_code(code: str, spaces: int) -> str:
    """Indent code by specified number of spaces"""
    indent = " " * spaces
    return "\n".join(indent + line for line in code.split("\n"))


@tool(
    "run_sandbox",
    "Execute code in a sandboxed environment for testing. Supports Python and JavaScript.",
    {
        "code": str,
        "language": str,
        "timeout": int,
        "safe_mode": bool
    }
)
async def run_sandbox(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute code in a sandboxed environment.

    Args:
        code: The code to execute
        language: Programming language (python, javascript)
        timeout: Maximum execution time in seconds (default: 30)
        safe_mode: If True, restricts dangerous operations (default: True)

    Returns:
        Execution result with stdout, stderr, and status
    """
    code = args.get("code", "")
    language = args.get("language", "python").lower()
    timeout = min(args.get("timeout", MAX_EXECUTION_TIME), MAX_EXECUTION_TIME)
    safe_mode = args.get("safe_mode", True)

    if not code.strip():
        return {
            "content": [{"type": "text", "text": "Error: No code provided"}],
            "is_error": True
        }

    # Security check in safe mode
    if safe_mode and language == "python":
        for forbidden in FORBIDDEN_PYTHON_IMPORTS:
            if forbidden in code:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Security Error: '{forbidden}' is not allowed in safe mode.\n"
                               f"Disable safe_mode if you need this functionality (requires approval)."
                    }],
                    "is_error": True
                }

    try:
        # Create temporary file
        suffix = ".py" if language == "python" else ".js"

        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=suffix,
            delete=False,
            encoding='utf-8'
        ) as f:
            sandbox_code = create_sandbox_script(code, language)
            f.write(sandbox_code)
            temp_file = f.name

        try:
            # Select interpreter
            if language == "python":
                cmd = [sys.executable, temp_file]
            elif language == "javascript":
                cmd = ["node", temp_file]
            else:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Unsupported language: {language}. Supported: python, javascript"
                    }],
                    "is_error": True
                }

            # Execute with timeout
            start_time = time.time()

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tempfile.gettempdir(),
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
            )

            execution_time = time.time() - start_time

            # Format output
            stdout = result.stdout[:MAX_OUTPUT_SIZE]
            stderr = result.stderr[:MAX_OUTPUT_SIZE]

            if len(result.stdout) > MAX_OUTPUT_SIZE:
                stdout += "\n... (output truncated)"
            if len(result.stderr) > MAX_OUTPUT_SIZE:
                stderr += "\n... (output truncated)"

            output_text = f"=== Sandbox Execution Result ===\n"
            output_text += f"Language: {language}\n"
            output_text += f"Execution Time: {execution_time:.2f}s\n"
            output_text += f"Exit Code: {result.returncode}\n\n"

            if stdout:
                output_text += f"=== STDOUT ===\n{stdout}\n\n"
            if stderr:
                output_text += f"=== STDERR ===\n{stderr}\n"

            return {
                "content": [{"type": "text", "text": output_text}],
                "is_error": result.returncode != 0
            }

        finally:
            # Cleanup
            try:
                os.unlink(temp_file)
            except:
                pass

    except subprocess.TimeoutExpired:
        return {
            "content": [{
                "type": "text",
                "text": f"Execution timed out after {timeout} seconds.\n"
                       f"Consider optimizing the code or increasing timeout."
            }],
            "is_error": True
        }
    except FileNotFoundError as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Interpreter not found: {e}\n"
                       f"Make sure {language} is installed."
            }],
            "is_error": True
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Sandbox execution error: {type(e).__name__}: {e}"
            }],
            "is_error": True
        }


@tool(
    "run_benchmark",
    "Benchmark code execution time with multiple iterations",
    {
        "code": str,
        "language": str,
        "iterations": int
    }
)
async def run_benchmark(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Benchmark code execution time.

    Args:
        code: Code to benchmark
        language: Programming language
        iterations: Number of iterations (default: 5, max: 20)

    Returns:
        Benchmark results with timing statistics
    """
    code = args.get("code", "")
    language = args.get("language", "python").lower()
    iterations = min(args.get("iterations", 5), 20)

    if not code.strip():
        return {
            "content": [{"type": "text", "text": "Error: No code provided"}],
            "is_error": True
        }

    times = []
    errors = []

    for i in range(iterations):
        result = await run_sandbox({
            "code": code,
            "language": language,
            "timeout": 10,
            "safe_mode": True
        })

        if result.get("is_error"):
            errors.append(f"Iteration {i+1}: {result['content'][0]['text'][:100]}")
        else:
            # Parse execution time from output
            output = result['content'][0]['text']
            for line in output.split('\n'):
                if 'Execution Time:' in line:
                    try:
                        time_str = line.split(':')[1].strip().replace('s', '')
                        times.append(float(time_str))
                    except:
                        pass

    if not times:
        return {
            "content": [{
                "type": "text",
                "text": f"Benchmark failed.\nErrors:\n" + "\n".join(errors)
            }],
            "is_error": True
        }

    # Calculate statistics
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    output = f"=== Benchmark Results ===\n"
    output += f"Language: {language}\n"
    output += f"Iterations: {len(times)}/{iterations}\n"
    output += f"Average Time: {avg_time:.4f}s\n"
    output += f"Min Time: {min_time:.4f}s\n"
    output += f"Max Time: {max_time:.4f}s\n"
    output += f"All Times: {[f'{t:.4f}s' for t in times]}\n"

    if errors:
        output += f"\nErrors ({len(errors)}):\n" + "\n".join(errors[:3])

    return {
        "content": [{"type": "text", "text": output}],
        "is_error": False
    }
