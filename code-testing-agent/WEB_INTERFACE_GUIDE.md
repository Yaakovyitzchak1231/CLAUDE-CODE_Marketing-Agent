# Web Interface Guide

## Overview

The Code Testing Agent now includes a **real-time web-based streaming interface** that lets you watch the agent work in your browser! No more staring at loading screens - you'll see every thought, tool usage, and result as it happens.

## Features

### 🎯 Real-Time Streaming
- See agent thoughts as they happen
- Watch tool executions in real-time
- Get instant feedback on results
- No page refreshing needed - uses Server-Sent Events (SSE)

### 📊 Live Statistics Dashboard
- **Events Received**: Total number of agent actions
- **Tools Used**: Count of tool invocations
- **Errors**: Any failures or issues
- **Runtime**: Live timer showing how long the agent has been running

### 🎨 Color-Coded Event Types
- **🤖 Agent Thinking (Cyan)**: Normal reasoning and planning
- **💭 Deep Thinking (Magenta)**: Extended reasoning blocks
- **🔧 Using Tool (Yellow)**: Tool invocations with parameters
- **✅ Tool Result (Green)**: Successful tool results
- **❌ Tool Error (Red)**: Failed operations
- **⚙️ System (Gray)**: System messages and status updates

### 💻 Beautiful UI
- Gradient purple background
- Smooth animations for new events
- Auto-scrolling to latest events
- Responsive design (works on mobile too!)
- Dark theme optimized for long viewing sessions

## Quick Start

### Option 1: Windows Batch File (Easiest)
```bash
run_with_web.bat
```

This will:
1. Start the web server on port 5000
2. Launch the agent with web streaming enabled
3. Open the default browser automatically (or navigate to http://localhost:5000)

### Option 2: Command Line
```bash
python agent.py --config configs/marketing-agent.yaml --web
```

Then open your browser to: **http://localhost:5000**

### Option 3: Custom Port
```bash
python agent.py --config configs/marketing-agent.yaml --web --web-port 8080
```

Access at: **http://localhost:8080**

## What You'll See

### When You First Connect
- Connection status indicator (green = connected)
- Statistics dashboard showing zeros
- "Waiting for agent to start..." message

### During Agent Execution

**Example Flow:**

1. **Agent Thinking** (Cyan Panel)
   ```
   🤖 Agent Thinking
   I'm going to start by mapping the project structure using Glob to find all Python files...
   ```

2. **Using Tool** (Yellow Panel)
   ```
   🔧 Using Tool
   Tool: Glob
   Input:
     pattern: **/*.py
     path: .
   ```

3. **Tool Result** (Green Panel)
   ```
   ✅ Tool Result
   Found 47 Python files:
   - agent.py
   - config.py
   - core/main_agent.py
   ...
   ```

4. **Agent Thinking** (Cyan Panel)
   ```
   🤖 Agent Thinking
   I found 47 Python files. Now I'll search for AI/LLM integration points...
   ```

5. **Deep Thinking** (Magenta Panel) - if model supports extended thinking
   ```
   💭 Deep Thinking
   Let me analyze the patterns I'm seeing... The langchain-service directory
   contains the main LLM integration code...
   ```

### Statistics Updates
Watch the top statistics cards update in real-time:
- **Events Received**: Increments with each action
- **Tools Used**: Increments when tools are called
- **Errors**: Increments if something fails
- **Runtime**: Live timer (MM:SS format)

## Technical Details

### Architecture
- **Backend**: Flask server with Server-Sent Events (SSE)
- **Frontend**: Vanilla JavaScript with EventSource API
- **Threading**: Web server runs in daemon thread
- **Port**: Default 5000 (configurable with --web-port)

### Network Access
- **Local Only (default)**: Access from your machine only
- **Network Access**: Server binds to 0.0.0.0 so you can access from other devices on your network
  - Example: `http://192.168.1.100:5000` from another computer
  - Example: `http://your-computer-name:5000` from another device

### Browser Compatibility
- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Any modern browser with EventSource support

### Performance
- **Lightweight**: Minimal CPU/memory overhead
- **Efficient**: SSE streaming is more efficient than WebSockets for one-way data
- **Scalable**: Can handle multiple connected clients
- **Auto-reconnect**: Automatically reconnects if connection drops

## Troubleshooting

### Port Already in Use
```
Error: Address already in use
```

**Solution**: Use a different port
```bash
python agent.py --config configs/marketing-agent.yaml --web --web-port 8080
```

### Firewall Blocking
If you can't access from another device:
1. Check Windows Firewall settings
2. Allow Python through the firewall
3. Or run from Command Prompt as Administrator

### Events Not Showing
1. Check browser console for errors (F12)
2. Verify agent is running with `--web` flag
3. Try refreshing the page
4. Check that Flask and flask-cors are installed

### Connection Lost
- Web interface will show "Disconnected" status
- Will automatically attempt to reconnect every 5 seconds
- If agent completes, connection will close (this is normal)

## Tips & Tricks

### 1. Multiple Browser Windows
Open multiple browser tabs/windows to view the same stream - all will update simultaneously!

### 2. Screen Recording
The web interface is perfect for:
- Recording demos
- Sharing progress with team
- Documenting agent behavior
- Creating tutorials

### 3. Mobile Viewing
Access from your phone/tablet while the agent runs on your desktop:
1. Find your computer's IP address: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
2. Open browser on mobile: `http://YOUR_IP:5000`
3. Watch the agent work from anywhere in your house!

### 4. Long Running Tasks
The web interface is designed for long-running audits:
- Auto-scroll keeps you at the latest event
- Statistics help you track progress
- Runtime timer shows elapsed time
- Events are never lost (streamed in real-time)

### 5. Keep Interface Open After Completion
The agent will keep the web server running after completion so you can review the full log. Press Ctrl+C in the terminal to exit.

## Comparison: Web vs Terminal

| Feature | Web Interface | Terminal |
|---------|---------------|----------|
| Visual Appeal | 🎨 Beautiful gradient UI | ⬛ Plain text |
| Real-time Updates | ✅ Instant | ✅ Instant |
| Color Coding | ✅ 6 event types | ✅ 4 event types |
| Statistics | ✅ Live dashboard | ❌ None |
| Remote Access | ✅ Any device on network | ❌ Same machine only |
| Mobile Friendly | ✅ Responsive | ❌ Requires SSH |
| Scrollback | ✅ Unlimited | ⚠️ Buffer limited |
| Recording | ✅ Browser recording | ⚠️ Terminal recording |

## Advanced Usage

### Custom Task with Web Interface
```bash
python agent.py \
  --config configs/marketing-agent.yaml \
  --web \
  --task "Test all API endpoints for security vulnerabilities"
```

### Production Deployment
For production use (not recommended for security reasons, but possible):
```python
# Edit web_server.py
if __name__ == '__main__':
    run_server(host='0.0.0.0', port=80)  # Requires admin/root
```

### Integration with CI/CD
You can run the web interface in CI/CD pipelines:
```yaml
# Example GitHub Actions
- name: Run Code Testing Agent
  run: |
    python agent.py --config configs/default.yaml --web &
    # Your test commands here
```

## Future Enhancements

Planned features for the web interface:
- [ ] Historical logs viewer
- [ ] Export to PDF/HTML
- [ ] Pause/resume functionality
- [ ] Filter events by type
- [ ] Search within events
- [ ] Dark/light theme toggle
- [ ] WebSocket support for bi-directional communication
- [ ] Real-time file diff viewer
- [ ] Interactive tool parameter editing

## Support

If you encounter issues with the web interface:
1. Check this guide first
2. Verify all dependencies are installed: `pip install -r requirements.txt`
3. Try the terminal version first: `python agent.py --config configs/marketing-agent.yaml`
4. Open an issue on GitHub with:
   - Python version
   - Browser and version
   - Error messages from terminal
   - Error messages from browser console (F12)

## Feedback

We'd love to hear your feedback on the web interface! Please share:
- What you love ❤️
- What could be better 🔧
- Feature requests 💡
- Bug reports 🐛

Enjoy watching your Code Testing Agent work in real-time! 🚀
