from claude_agent_sdk import tool
from typing import Any, Dict
import ast
import radon.complexity as radon_cc
from pathlib import Path

@tool(
    "analyze_python_file",
    "Analyze Python file structure: functions, classes, imports, complexity",
    {"file_path": str}
)
async def analyze_python_file(args: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Python file with AST and calculate complexity metrics"""
    try:
        file_path = Path(args["file_path"])
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source)

        functions = []
        classes = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    imports.extend([alias.name for alias in node.names])
                else:
                    imports.append(node.module if node.module else "")

        # Calculate complexity
        cc_results = radon_cc.cc_visit(source)
        avg_complexity = sum(c.complexity for c in cc_results) / len(cc_results) if cc_results else 0

        result = {
            "file": str(file_path),
            "functions": functions,
            "classes": classes,
            "imports": list(set(imports)),
            "complexity": {
                "average": round(avg_complexity, 2),
                "total_functions": len(cc_results),
                "high_complexity": [c.name for c in cc_results if c.complexity > 10]
            }
        }

        return {
            "content": [{
                "type": "text",
                "text": f"Analysis of {file_path.name}:\n" +
                       f"Functions: {len(functions)}\n" +
                       f"Classes: {len(classes)}\n" +
                       f"Imports: {len(imports)}\n" +
                       f"Avg Complexity: {result['complexity']['average']}\n" +
                       f"High Complexity Functions: {', '.join(result['complexity']['high_complexity']) or 'None'}"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error analyzing file: {str(e)}"
            }],
            "is_error": True
        }
