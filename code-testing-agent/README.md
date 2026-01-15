# Code Testing Agent

A sophisticated Claude Agent SDK application for auditing codebases, testing for issues (including AI hallucinations), creating fixes, and automatically submitting GitHub PRs.

## Features

- **Comprehensive Codebase Auditing**: Examines every file, function, and dependency
- **Hallucination Detection**: Verifies AI/LLM outputs don't fabricate data
- **Automated Fix Generation**: Creates tested fixes for identified issues
- **GitHub Integration**: Automatically creates PRs with detailed descriptions
- **Configurable**: YAML-based configuration for any project

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

## Configuration

Edit `configs/marketing-agent.yaml` to customize:
- Project paths
- GitHub settings
- Test commands
- Analysis patterns
- Agent behavior

## Architecture

- **Main Agent**: Orchestrates workflow and delegates to subagents
- **Subagents**:
  - `hallucination_detector`: Tests AI outputs for fabricated data
  - `fix_generator`: Creates tested fixes for root causes
  - `pr_manager`: Manages GitHub PRs with detailed descriptions
- **Custom Tools**:
  - GitHub API integration
  - Python AST analysis
  - Test execution
  - Code metrics

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

## Expansion

After the MVP is working, you can expand with:
1. Additional subagents (codebase_analyzer, dependency_auditor, security_auditor)
2. More tools (browser automation, dependency graphing)
3. Enhanced reporting (HTML reports, dashboards)
4. CI/CD integration (GitHub Actions)

## License

MIT License
