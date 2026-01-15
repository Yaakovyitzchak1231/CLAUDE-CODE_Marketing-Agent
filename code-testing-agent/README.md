# Code Testing Agent

A sophisticated Claude Agent SDK application for auditing codebases, testing for issues (including AI hallucinations), creating fixes, and automatically submitting GitHub PRs.

## Features

- **Comprehensive Codebase Auditing**: Examines every file, function, and dependency
- **Hallucination Detection**: Verifies AI/LLM outputs don't fabricate data
- **Automated Fix Generation**: Creates tested fixes for identified issues
- **GitHub Integration**: Automatically creates PRs with detailed descriptions
- **Real-Time Web Interface**: Live streaming dashboard to watch the agent work
- **Human-in-the-Loop**: Approval system for critical actions (file changes, PRs, code execution)
- **9 Specialized Sub-Agents**: Security, performance, browser testing, and more
- **Advanced Testing Tools**: Sandboxed code execution, Playwright browser automation, API testing
- **Directory Selection**: Analyze any directory from the web interface
- **Configurable**: YAML-based configuration for any project

## Interactive Web Interface

The Code Testing Agent includes a **fully interactive web dashboard** where you can watch AND control the agent in real-time!

### Features
- 💬 **Two-way interaction** - Send messages, ask questions, give instructions
- 🎮 **Agent control** - Interrupt or stop execution anytime
- 🤖 **Live streaming** of agent thoughts and actions
- 🔧 **Tool usage** monitoring with parameters and results
- 📊 **Real-time statistics** (events, tools used, errors, runtime)
- ⏳ **Smart waiting** - Agent prompts when it needs your input
- 🎨 **Beautiful UI** with color-coded event types
- 📱 **Responsive design** works on desktop and mobile

### What You Can Do
- **Guide the agent** as it works
- **Answer questions** when agent needs clarification
- **Change directions** mid-task with the interrupt button
- **Send follow-up** prompts based on findings
- **Stop execution** if it's going the wrong way
- **Watch from anywhere** - access from phone/tablet on same network

### Quick Start with Web Interface

**Option 1: Using the convenience script (Windows)**
```bash
run_with_web.bat
```

**Option 2: Command line**
```bash
python agent.py --config configs/marketing-agent.yaml --web
```

Then open your browser to: **http://localhost:5000**

**The agent will wait for YOUR first instruction!** You'll see:
- 👋 "I'm ready to help!" prompt
- Text input field (auto-focused)
- Type your task and press Ctrl+Enter or click Send

**Example first instructions:**
- "Audit the authentication module for security issues"
- "Find all Python files and analyze their complexity"
- "Test the API endpoints for common vulnerabilities"
- "Check if any AI components are hallucinating"

Once you send your first message, you'll see:
- Agent thinking (cyan) 🤖
- Deep thinking (magenta) 💭
- Tool usage (yellow) 🔧
- Results (green/red) ✅❌
- Live statistics and runtime counter

### Custom Port
```bash
python agent.py --config configs/marketing-agent.yaml --web --web-port 8080
```

## Setup

### Prerequisites
- Python 3.10+
- Claude Code CLI installed
- GitHub personal access token

### Installation

```bash
cd code-testing-agent

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your tokens

# Set API key
export ANTHROPIC_API_KEY=your_api_key_here
export GITHUB_TOKEN=your_github_token_here
```

### GitHub Token Setup

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Select scopes:
   - `repo` (all)
   - `workflow`
4. Generate token and copy it
5. Add to .env: `GITHUB_TOKEN=ghp_xxxxx`

## Usage

### Full Audit
```bash
python agent.py --config configs/marketing-agent.yaml
```

### Custom Task
```bash
python agent.py --config configs/marketing-agent.yaml --task "Test for SQL injection vulnerabilities"
```

### Analyze a Different Directory
```bash
# From command line
python agent.py --config configs/default.yaml --directory /path/to/your/project

# Or from the web interface - use the directory selector panel
```

### Install Browser Automation (Playwright)
```bash
# Install Playwright browsers (required for browser testing)
playwright install chromium
```

## Configuration

Edit `configs/marketing-agent.yaml` to customize:
- Project paths
- GitHub settings
- Test commands
- Analysis patterns
- Agent behavior

## Architecture

- **Main Agent**: Orchestrates workflow and delegates to subagents
- **9 Specialized Subagents**:
  - `codebase_analyzer`: Maps project structure, architecture, and patterns
  - `security_auditor`: Finds vulnerabilities, secrets, injection flaws
  - `dependency_auditor`: Analyzes dependencies for CVEs and updates
  - `performance_analyzer`: Identifies bottlenecks (N+1 queries, memory issues)
  - `integration_tester`: Tests API endpoints and service integrations
  - `browser_tester`: UI/UX testing with Playwright browser automation
  - `hallucination_detector`: Tests AI outputs for fabricated data
  - `fix_generator`: Creates tested fixes for root causes
  - `pr_manager`: Manages GitHub PRs with detailed descriptions
- **Custom Tools**:
  - GitHub API integration (PR creation, listing)
  - Python AST analysis (complexity, structure)
  - Test execution (run tests, capture output)
  - **Sandboxed Code Execution** (safe Python/JS execution)
  - **Browser Automation** (Playwright UI testing, screenshots)
  - **API Testing** (HTTP requests, test suites, health checks)
- **Human-in-the-Loop System**:
  - Approval required for file modifications
  - Approval required for PR creation
  - Approval required for code execution
  - Configurable auto-approve for safe actions

## Output

Reports are saved to `reports/[timestamp]/`:
- `report.md`: Markdown summary
- `findings.json`: Structured data
- `prs.txt`: PR URLs

## Troubleshooting

**"GITHUB_TOKEN not set"**
```bash
export GITHUB_TOKEN=your_token_here
```

**"Claude Code not found"**
Install Claude Code CLI: https://code.claude.com/docs/en/setup

**Type errors**
Run verification:
```bash
python -m py_compile agent.py
```

## Available Tools

The agent has access to these specialized tools:

### Code Analysis
- `analyze_python_file` - Parse Python files for structure, complexity, imports
- `run_tests` - Execute test commands and capture results

### Sandboxed Execution
- `run_sandbox` - Execute Python/JavaScript code safely with resource limits
- `run_benchmark` - Benchmark code execution time with multiple iterations

### Browser Automation
- `browser_test` - Automate browser interactions (click, fill, screenshot)
- `browser_screenshot` - Take screenshots of web pages

### API Testing
- `api_test` - Make HTTP requests with assertions
- `api_test_suite` - Run multiple API tests in sequence
- `health_check` - Check health of multiple service endpoints

### GitHub
- `create_pull_request` - Create PRs with detailed descriptions
- `list_pull_requests` - List open/closed PRs

## Future Expansion

Potential enhancements:
1. Enhanced reporting (HTML reports, dashboards)
2. CI/CD integration (GitHub Actions workflow)
3. Additional language support (TypeScript, Go, Rust)
4. Database testing capabilities
5. Load testing integration

## License

MIT License
