"""
Fore-Poster Scheduled Task Manager

This module provides background task scheduling functionality for Fore-Poster,
including automatic posting of scheduled content and sending notifications.
It uses APScheduler to manage the scheduled tasks and handles AWS SES for email
notifications in production environments.

Usage:
    python fore_scheduler.py [--env-file ENV_FILE_PATH]
    
Arguments:
    --env-file PATH           Path to a custom .env file
    
Environment Variables:
    APP_ENV: Application environment (development, testing, production)
    SCHEDULER_INTERVAL_MINUTES: Time between checks for scheduled posts (default: 1)
    SCHEDULER_ADVANCE_MINUTES: How many minutes ahead to consider posts for processing (default: 1)
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from sqlalchemy import and_
import signal
import atexit
import time
import os
import logging
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Parse command line arguments
def parse_args():
    parser = argparse.ArgumentParser(description='Fore-Poster Scheduler')
    parser.add_argument('--env-file', type=str, help='Path to environment file')
    return parser.parse_args()

# Load local app components
from env_handler import load_environment
args = parse_args()
if args.env_file:
    logger.info(f"Loading environment from: {args.env_file}")
    load_environment(args.env_file)

from fore_poster import app, db, Post, XClient
from config import Config
# Import SSE Manager for real-time updates
try:
    from sse_manager import SSEManager
    has_sse = True
    logger.info("SSE support enabled for real-time updates")
except ImportError:
    has_sse = False
    logger.info("SSE support not available")

# Import shared modules - Only import functions, not the notifier yet
from core.notification import init_notifier, get_notifier
from core.posting import post_to_platform

# Get scheduler configuration from environment variables
from env_handler import get_env_var
SCHEDULER_INTERVAL_MINUTES = int(get_env_var('SCHEDULER_INTERVAL_MINUTES', '1'))
SCHEDULER_ADVANCE_MINUTES = int(get_env_var('SCHEDULER_ADVANCE_MINUTES', '1'))

class PostScheduler:
    """
    Manages the scheduling and processing of posts.
    
    This class is responsible for checking for scheduled posts,
    processing them through the appropriate platform client,
    and sending notifications about the results.
    """
    def __init__(self):
        """Initialize the scheduler and supporting components."""
        self.scheduler = BackgroundScheduler()
        self.x_client = XClient()
        self.running = False
        self.notifier = None  # Will be set by main()
        
    def start(self):
        """
        Start the scheduler to process posts.
        
        This sets up the job to check for scheduled posts at the specified interval
        and registers shutdown handlers for graceful termination.
        """
        # Add the job to check for scheduled posts
        self.scheduler.add_job(
            func=self.check_scheduled_posts,
            trigger=IntervalTrigger(minutes=SCHEDULER_INTERVAL_MINUTES),
            id='check_posts',
            name='Check scheduled posts'
        )
        
        # Register shutdown handlers
        self.register_shutdown_handlers()
        
        # Start the scheduler
        self.scheduler.start()
        self.running = True
        logger.info(f"Scheduler started with interval of {SCHEDULER_INTERVAL_MINUTES} minute(s)")
        
    def register_shutdown_handlers(self):
        """Register signal handlers and exit functions for graceful shutdown."""
        # Define signal handler
        def shutdown_handler(signum, frame):
            logger.info(f"Received shutdown signal: {signum}")
            self.shutdown()
        
        # Register for common termination signals
        signal.signal(signal.SIGINT, shutdown_handler)  # Ctrl+C
        signal.signal(signal.SIGTERM, shutdown_handler) # Termination
        
        # Register with atexit to ensure cleanup on normal exit
        atexit.register(self.shutdown)
        
        logger.info("Registered shutdown handlers")
    
    def shutdown(self):
        """
        Gracefully shut down the scheduler.
        
        This ensures all jobs complete and resources are properly cleaned up.
        """
        if self.running:
            logger.info("Shutting down scheduler...")
            self.scheduler.shutdown(wait=True)
            self.running = False
            logger.info("Scheduler has been shut down")
        
    def check_scheduled_posts(self):
        """
        Check for and process scheduled posts.
        
        This function finds posts scheduled for the near future and processes them.
        """
        with app.app_context():
            now = datetime.utcnow()
            upcoming = now + timedelta(minutes=SCHEDULER_ADVANCE_MINUTES)
            logger.info(f"Checking for posts scheduled before {upcoming}")
            
            posts = Post.query.filter(
                and_(
                    Post.status == 'scheduled',
                    Post.scheduled_time <= upcoming
                )
            ).all()
            
            logger.info(f"Found {len(posts)} posts to process")
            for post in posts:
                logger.info(f"Processing post {post.id}: {post.content[:30]}...")
                self.process_post(post)
                
    def process_post(self, post):
        """
        Process a single scheduled post.
        
        Args:
            post: The Post object to process and publish
        """
        try:
            # Check if post has an image
            image_path = None
            if post.image_filename:
                # Get absolute path to instance folder
                from flask import current_app
                instance_path = current_app.instance_path
                image_path = os.path.join(instance_path, 'uploads', post.image_filename)
                logger.info(f"Post has image: {image_path}")
            
            # Use shared posting functionality with the properly initialized notifier
            # Get a fresh reference to the notifier in case we need it later
            notifier = get_notifier()
            result = post_to_platform(post, self.x_client, image_path)
            
            if result['success']:
                # Update post status
                post.status = 'posted'
                post.post_id = result['post_id']
                db.session.commit()
                
                # Send real-time update if SSE is available
                if has_sse:
                    try:
                        # Convert the post to a dictionary for sending
                        post_dict = {
                            'id': post.id,
                            'content': post.content,
                            'scheduled_time': post.scheduled_time.isoformat() if isinstance(post.scheduled_time, datetime) else post.scheduled_time,
                            'status': post.status,
                            'platform': post.platform,
                            'post_id': post.post_id,
                            'image_url': post.image_url,
                            'image_filename': post.image_filename
                        }
                        SSEManager.event_queue.put(post_dict)
                        logger.info(f"Queued real-time update for post {post.id}")
                    except Exception as e:
                        logger.error(f"Failed to send real-time update: {str(e)}")
            else:
                # Update post status
                post.status = 'failed'
                db.session.commit()
                
                # Send real-time update if SSE is available
                if has_sse:
                    try:
                        # Convert the post to a dictionary for sending
                        post_dict = {
                            'id': post.id,
                            'content': post.content,
                            'scheduled_time': post.scheduled_time.isoformat() if isinstance(post.scheduled_time, datetime) else post.scheduled_time,
                            'status': post.status,
                            'platform': post.platform,
                            'post_id': post.post_id,
                            'image_url': post.image_url,
                            'image_filename': post.image_filename
                        }
                        SSEManager.event_queue.put(post_dict)
                        logger.info(f"Queued real-time update for post {post.id}")
                    except Exception as e:
                        logger.error(f"Failed to send real-time update: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error processing post {post.id}: {str(e)}")
            
            # Send notification through shared notifier
            notifier = get_notifier()
            notifier.send_notification(
                subject="Scheduler Error",
                message=f"Error processing post {post.id}: {str(e)}"
            )

def main():
    """Main entry point for the scheduler."""
    app_env = os.getenv('APP_ENV', 'development')
    logger.info(f"Starting scheduler in {app_env} environment")
    logger.info(f"Using interval of {SCHEDULER_INTERVAL_MINUTES} minute(s)")
    
    # Initialize configuration
    Config.init_app(app_env)
    
    # Initialize the notifier with the correct configuration
    notifier = init_notifier()
    
    # Start scheduler
    scheduler = PostScheduler()
    
    # Make notifier available to the scheduler
    scheduler.notifier = notifier
    
    scheduler.start()
    
    # Keep main thread alive while scheduler runs in background
    try:
        while scheduler.running:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        logger.info("Exiting main thread")

if __name__ == "__main__":
    main()