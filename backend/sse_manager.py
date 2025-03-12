"""
Server-Sent Events (SSE) Manager for Fore-Poster

This module adds real-time update capabilities to Fore-Poster by implementing
Server-Sent Events. This allows the backend to push updates to the frontend
when posts are processed by the scheduler.

Usage:
- Import the SSEManager class where post status changes occur
- Call SSEManager.send_update() with the updated post information
- Frontend can subscribe to the /api/events endpoint to receive updates
"""
import json
import queue
import threading
from flask import Blueprint, Response, stream_with_context
import logging

# Set up logging
logger = logging.getLogger(__name__)

class SSEManager:
    """Manages Server-Sent Events for real-time updates"""
    
    # Class-level queue for events
    event_queue = queue.Queue()
    # Dict to track active clients
    clients = {}
    # Lock to protect client list during thread access
    clients_lock = threading.Lock()
    # Next client ID
    next_client_id = 0
    
    @classmethod
    def setup_routes(cls, app):
        """Set up the SSE endpoint in the Flask app"""
        events_bp = Blueprint('events', __name__)
        
        @events_bp.route('/events')
        def events():
            """SSE endpoint that sends real-time updates to clients"""
            def generate():
                # Register this client
                with cls.clients_lock:
                    client_id = cls.next_client_id
                    cls.next_client_id += 1
                    # Create a queue for this client
                    client_queue = queue.Queue()
                    cls.clients[client_id] = client_queue
                
                logger.info(f"Client {client_id} connected to SSE")
                
                # Initial connection established message
                yield "data: {\"type\": \"connected\"}\n\n"
                
                try:
                    while True:
                        # Get next message for this client (blocking with timeout)
                        try:
                            message = client_queue.get(timeout=30)
                            yield f"data: {message}\n\n"
                        except queue.Empty:
                            # Send a heartbeat every 30 seconds
                            yield "data: {\"type\": \"heartbeat\"}\n\n"
                finally:
                    # Clean up when client disconnects
                    with cls.clients_lock:
                        if client_id in cls.clients:
                            del cls.clients[client_id]
                    logger.info(f"Client {client_id} disconnected from SSE")
            
            return Response(
                stream_with_context(generate()),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'X-Accel-Buffering': 'no'  # Disable buffering for nginx
                }
            )
        
        # Register the blueprint
        app.register_blueprint(events_bp, url_prefix='/api')
    
    @classmethod
    def send_update(cls, post_data):
        """
        Send an update about a post to all connected clients
        
        Args:
            post_data: Dictionary containing post data to send to clients
        """
        if not cls.clients:
            return
        
        # Prepare the update message
        message = json.dumps({
            "type": "post_update",
            "data": post_data
        })
        
        # Send to all clients
        with cls.clients_lock:
            for client_queue in cls.clients.values():
                client_queue.put(message)
        
        logger.info(f"Sent post update to {len(cls.clients)} clients")

# Background thread to process the event queue
def event_processor():
    """Background thread that processes the event queue and sends updates to all clients"""
    while True:
        try:
            # Get the next event from the queue (blocking)
            event = SSEManager.event_queue.get()
            
            # Process the event
            SSEManager.send_update(event)
            
            # Mark the task as done
            SSEManager.event_queue.task_done()
        except Exception as e:
            logger.error(f"Error processing SSE event: {str(e)}")

# Start the background thread when this module is imported
event_thread = threading.Thread(target=event_processor, daemon=True)
event_thread.start() 