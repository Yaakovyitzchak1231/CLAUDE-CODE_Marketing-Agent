#!/usr/bin/env python3
"""
Web server for streaming Code Testing Agent activity in real-time with interactive control
"""
from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS
import queue
import json
import threading
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Global queues for communication
event_queue = queue.Queue()
user_input_queue = queue.Queue()  # For user messages to agent
control_queue = queue.Queue()  # For control commands (pause, stop, etc.)

class StreamManager:
    """Manages streaming events to web clients"""

    def __init__(self):
        self.clients = []
        self.lock = threading.Lock()
        self.agent_status = "idle"  # idle, running, waiting_for_input, paused, stopped
        self.waiting_for_input = False
        self.conversation_history = []

    def add_client(self, client_queue):
        with self.lock:
            self.clients.append(client_queue)

    def remove_client(self, client_queue):
        with self.lock:
            if client_queue in self.clients:
                self.clients.remove(client_queue)

    def broadcast_event(self, event_type, data):
        """Broadcast event to all connected clients"""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }

        # Add to conversation history
        with self.lock:
            self.conversation_history.append(event)

            # Broadcast to all clients
            for client_queue in self.clients:
                try:
                    client_queue.put(event)
                except:
                    pass

    def set_agent_status(self, status):
        """Update agent status"""
        with self.lock:
            self.agent_status = status
        self.broadcast_event('status-change', {'status': status})

    def set_waiting_for_input(self, waiting, prompt=None):
        """Set whether agent is waiting for user input"""
        with self.lock:
            self.waiting_for_input = waiting

        if waiting and prompt:
            self.broadcast_event('input-request', {'prompt': prompt})

    def get_conversation_history(self):
        """Get conversation history"""
        with self.lock:
            return list(self.conversation_history)

stream_manager = StreamManager()

@app.route('/')
def index():
    """Serve the dashboard"""
    return render_template('dashboard.html')

@app.route('/stream')
def stream():
    """Server-Sent Events endpoint for real-time updates"""
    def event_generator():
        client_queue = queue.Queue()
        stream_manager.add_client(client_queue)

        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'message': 'Connected to Code Testing Agent'})}\n\n"

            while True:
                try:
                    event = client_queue.get(timeout=30)
                    yield f"data: {json.dumps(event)}\n\n"
                except queue.Empty:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
        finally:
            stream_manager.remove_client(client_queue)

    return Response(event_generator(), mimetype='text/event-stream')

@app.route('/api/status')
def status():
    """Get current agent status"""
    return jsonify({
        'status': stream_manager.agent_status,
        'clients': len(stream_manager.clients),
        'waiting_for_input': stream_manager.waiting_for_input,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/send_message', methods=['POST'])
def send_message():
    """Send a message to the agent"""
    data = request.json
    message = data.get('message', '')

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    # Add to user input queue
    user_input_queue.put({
        'type': 'user_message',
        'message': message,
        'timestamp': datetime.now().isoformat()
    })

    # Broadcast to all clients so they can see it
    stream_manager.broadcast_event('user-message', {
        'text': message,
        'from': 'user'
    })

    return jsonify({'success': True})

@app.route('/api/control', methods=['POST'])
def control():
    """Send control commands (pause, resume, stop)"""
    data = request.json
    command = data.get('command', '')

    if command not in ['pause', 'resume', 'stop', 'interrupt']:
        return jsonify({'error': 'Invalid command'}), 400

    control_queue.put({
        'command': command,
        'timestamp': datetime.now().isoformat()
    })

    stream_manager.broadcast_event('system', {
        'text': f'Control command: {command}'
    })

    return jsonify({'success': True, 'command': command})

@app.route('/api/history')
def history():
    """Get conversation history"""
    return jsonify({
        'history': stream_manager.get_conversation_history(),
        'total': len(stream_manager.get_conversation_history())
    })

@app.route('/api/set_directory', methods=['POST'])
def set_directory():
    """Set the target directory for analysis"""
    import os
    data = request.json
    directory = data.get('directory', '')

    if not directory:
        return jsonify({'error': 'No directory provided'}), 400

    # Validate directory exists
    if not os.path.exists(directory):
        return jsonify({'error': f'Directory not found: {directory}'}), 400

    if not os.path.isdir(directory):
        return jsonify({'error': f'Not a directory: {directory}'}), 400

    # Store the directory for the agent to use
    stream_manager.target_directory = directory

    # Notify agent via user input queue
    user_input_queue.put({
        'type': 'set_directory',
        'directory': directory,
        'timestamp': datetime.now().isoformat()
    })

    stream_manager.broadcast_event('system', {
        'text': f'Target directory set to: {directory}'
    })

    return jsonify({'success': True, 'directory': directory})

@app.route('/api/approval_response', methods=['POST'])
def approval_response():
    """Handle user approval responses"""
    data = request.json
    request_id = data.get('request_id', '')
    approved = data.get('approved', False)
    modifications = data.get('modifications')

    if not request_id:
        return jsonify({'error': 'No request_id provided'}), 400

    # Add approval response to queue
    user_input_queue.put({
        'type': 'approval_response',
        'request_id': request_id,
        'approved': approved,
        'modifications': modifications,
        'timestamp': datetime.now().isoformat()
    })

    status_text = 'approved' if approved else 'rejected'
    stream_manager.broadcast_event('system', {
        'text': f'Action {status_text}'
    })

    return jsonify({'success': True, 'approved': approved})

def publish_event(event_type, data):
    """Publish event to all connected clients"""
    stream_manager.broadcast_event(event_type, data)

def set_agent_status(status):
    """Update agent status"""
    stream_manager.set_agent_status(status)

def request_user_input(prompt):
    """Request user input"""
    stream_manager.set_waiting_for_input(True, prompt)

def get_user_input(timeout=None):
    """Get user input from queue"""
    try:
        return user_input_queue.get(timeout=timeout)
    except queue.Empty:
        return None

def get_control_command(timeout=0):
    """Check for control commands"""
    try:
        return control_queue.get(timeout=timeout)
    except queue.Empty:
        return None

def run_server(host='127.0.0.1', port=5000):
    """Run the Flask server"""
    print(f"Starting web server at http://{host}:{port}")
    print(f"Open your browser to see the live stream!")
    app.run(host=host, port=port, debug=False, threaded=True)

if __name__ == '__main__':
    run_server()
