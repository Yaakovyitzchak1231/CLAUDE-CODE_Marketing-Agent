# Interactive Web Interface Guide

## Overview

The Code Testing Agent web interface now supports **full two-way interaction**! You can:
- 💬 Send messages and prompts to the agent
- ❓ Respond to agent questions
- 🛑 Control agent execution (interrupt, stop)
- 📺 Watch everything happen in real-time

## How to Start

```bash
cd code-testing-agent
python agent.py --config configs/marketing-agent.yaml --web
```

Open browser: **http://localhost:5000**

## Interactive Features

### 1. **Send Messages to Agent** 💬

The right panel has a text input where you can:
- Send new instructions
- Ask questions
- Provide additional context
- Respond to agent prompts

**How to use:**
1. Type your message in the text area
2. Click "📤 Send Message" or press **Ctrl+Enter**
3. Your message appears in the stream with green border
4. Agent processes it and responds

**Example interactions:**
```
You: "Now check the security of the API endpoints"
Agent: "I'll analyze all API endpoints for security vulnerabilities..."

You: "Focus on the authentication endpoints first"
Agent: "Analyzing authentication endpoints..."

You: "What have you found so far?"
Agent: "I've found 3 potential issues..."
```

### 2. **Control Agent Execution** 🎮

Two control buttons let you manage the agent:

**⏸️ Interrupt Button**
- Pauses agent and waits for your input
- Use when you want to give new directions
- Agent will wait for your next message
- Great for course correction mid-task

**⏹️ Stop Button**
- Immediately stops agent execution
- Useful if agent is going in wrong direction
- Cannot resume after stopping (must restart)

**How to use:**
```
1. Click "⏸️ Interrupt"
   → Agent pauses
   → Yellow indicator shows "Agent is waiting for your response"
   → Type your message
   → Agent resumes with your new instructions

2. Click "⏹️ Stop"
   → Agent stops completely
   → Web interface remains open for review
```

### 3. **Real-Time Conversation** 💭

The interface shows both sides of the conversation:

**Agent messages** (colored panels):
- 🤖 Cyan: Agent thinking
- 💭 Magenta: Deep reasoning
- 🔧 Yellow: Tool usage
- ✅ Green: Successful results
- ❌ Red: Errors

**Your messages** (green border):
- 💬 Shows "You" as the sender
- Displays your exact message
- Timestamp for reference

### 4. **Waiting Indicator** ⏳

When agent needs your input:
- Yellow box appears: "⏳ Agent is waiting for your response..."
- Input field automatically focuses
- Send your response to continue

## Common Use Cases

### 1. **Guided Exploration**
```
Initial: "Analyze the codebase"
Agent: "I'll start by mapping the structure..."
[After reviewing results]
You: "Now focus on the authentication module"
Agent: "Analyzing authentication..."
You: "Check for SQL injection vulnerabilities"
Agent: "Testing for SQL injection..."
```

### 2. **Clarifying Instructions**
```
Agent: "I found 5 different test files. Which should I run?"
You: "Run the integration tests first"
Agent: "Running integration tests..."
```

### 3. **Course Correction**
```
Agent: "I'm analyzing all 1000 files..."
You: [Click Interrupt]
You: "Only analyze Python files in the src/ directory"
Agent: "Focusing on src/ directory Python files..."
```

### 4. **Follow-up Questions**
```
Agent: "Audit complete. Found 3 issues."
You: "Can you explain the severity of each issue?"
Agent: "Issue 1: CRITICAL - SQL injection..."
You: "Create a PR to fix Issue 1"
Agent: "Creating fix for SQL injection..."
```

### 5. **Interactive Testing**
```
You: "Test the login endpoint"
Agent: "Testing login endpoint..."
Agent: "Login works. Should I test logout?"
You: "Yes, test logout and session management"
Agent: "Testing logout and sessions..."
```

## Keyboard Shortcuts

- **Ctrl+Enter** (or **Cmd+Enter** on Mac): Send message
- **Tab**: Focus input field
- **Escape**: Clear input field (custom - add if needed)

## Tips & Best Practices

### 1. **Be Specific**
Instead of: "Check that"
Try: "Check the authentication module for security issues"

### 2. **Use Interrupt for Major Changes**
- Don't wait for agent to finish long task
- Click Interrupt immediately
- Give new clear instructions

### 3. **Ask for Status Updates**
```
You: "What are you working on now?"
You: "What have you found so far?"
You: "How many files have you checked?"
```

### 4. **Break Down Complex Tasks**
Instead of one huge prompt, interact step by step:
```
You: "First, map the project structure"
[Wait for results]
You: "Now find all API endpoints"
[Wait for results]
You: "Test those endpoints for security"
```

### 5. **Review Before Acting**
```
Agent: "I found 10 issues. Should I create PRs for all?"
You: "Show me the issues first"
[Review issues]
You: "Create PRs for issues 1, 3, and 5 only"
```

## Advanced Features

### 1. **Multi-Turn Conversations**
The agent maintains context across messages:
```
You: "Analyze the database module"
Agent: "The database uses SQLAlchemy..."
You: "Are there any N+1 query issues?"
Agent: "Yes, I found 3 N+1 queries in..."
You: "Fix the most critical one"
Agent: "Creating fix for the User query..."
```

### 2. **Branching Discussions**
```
Agent: "Found security issue in authentication"
You: "How severe is it?"
Agent: "CRITICAL - allows bypass..."
You: "Show me the vulnerable code"
Agent: [Shows code]
You: "Create a fix"
Agent: "Implementing fix..."
```

### 3. **Real-Time Collaboration**
Multiple people can watch the same stream (different browsers/devices):
- Everyone sees the same events
- Only one person should send messages (to avoid confusion)
- Great for pair programming or demos

## Troubleshooting

### Message Not Sending
1. Check connection status (green = connected)
2. Look for error in browser console (F12)
3. Verify web server is running
4. Try refreshing the page

### Agent Not Responding
1. Check terminal for errors
2. Verify agent is running (see terminal output)
3. Try interrupting and sending new message
4. If stuck, stop and restart

### Control Buttons Not Working
1. Verify you confirmed the action (popup dialog)
2. Check browser console for errors
3. Refresh page and try again

### Waiting Indicator Stuck
1. Send any message to continue
2. If still stuck, click Stop and restart
3. Check terminal for errors

## API Endpoints

For programmatic access:

**Send Message**
```bash
curl -X POST http://localhost:5000/api/send_message \
  -H "Content-Type: application/json" \
  -d '{"message": "Your message here"}'
```

**Control Agent**
```bash
curl -X POST http://localhost:5000/api/control \
  -H "Content-Type: application/json" \
  -d '{"command": "interrupt"}'
```

**Get Status**
```bash
curl http://localhost:5000/api/status
```

**Get History**
```bash
curl http://localhost:5000/api/history
```

## Security Notes

- Web server binds to 0.0.0.0 (accessible from network)
- No authentication by default (add if needed)
- Don't expose to public internet without security
- Use on trusted networks only

## Future Enhancements

Planned features:
- [ ] Message history search
- [ ] Save/load conversations
- [ ] File upload for context
- [ ] Voice input
- [ ] Agent personality settings
- [ ] Custom themes
- [ ] Mobile app
- [ ] Multi-agent chat rooms

## Getting Help

If you have questions or issues:
1. Check this guide
2. Review WEB_INTERFACE_GUIDE.md
3. Check browser console (F12)
4. Check terminal output
5. Open GitHub issue

Enjoy interacting with your Code Testing Agent! 🚀
