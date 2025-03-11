"""
Fore-Poster Scheduled Task Manager

This module provides background task scheduling functionality for Fore-Poster,
including automatic posting of scheduled content and sending notifications.
It uses APScheduler to manage the scheduled tasks and handles AWS SES for email
notifications in production environments.

Usage:
    python fore_scheduler.py  # Run as a standalone process
    
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

# Load local app components
from fore_poster import app, db, Post, XClient
from env_handler import get_env_var
from config import Config

# Get scheduler configuration from environment variables
SCHEDULER_INTERVAL_MINUTES = int(get_env_var('SCHEDULER_INTERVAL_MINUTES', '1'))
SCHEDULER_ADVANCE_MINUTES = int(get_env_var('SCHEDULER_ADVANCE_MINUTES', '1'))

class NotificationHandler:
    """
    Handles sending notifications about post status.
    
    In production, uses AWS SES to send email notifications.
    In development, just logs the notifications.
    """
    def __init__(self):
        """Initialize notification handler based on environment."""
        self.production = Config.PRODUCTION
        if self.production:
            import boto3
            self.ses = boto3.client('ses', region_name=Config.AWS_REGION)
            self.sender = Config.SES_SENDER
            self.recipient = Config.SES_RECIPIENT
            logger.info(f"Notification handler initialized in production mode")
        else:
            logger.info(f"Notification handler initialized in development mode (notifications will be logged only)")

    def send_notification(self, subject: str, message: str):
        """
        Send a notification about post status.
        
        Args:
            subject: Subject line for the notification
            message: Body text for the notification
        """
        if not self.production:
            logger.info(f"Development mode - would send email: {subject}")
            logger.info(f"Message: {message}")
            return

        try:
            self.ses.send_email(
                Source=self.sender,
                Destination={'ToAddresses': [self.recipient]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': message}}
                }
            )
            logger.info(f"Email sent: {subject}")
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")

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
        self.notifier = NotificationHandler()
        self.running = False
        
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
                # Check if the image file exists
                if not os.path.exists(image_path):
                    logger.warning(f"Image file not found at {image_path}")
                    image_path = None
            
            # Post with or without image
            result = self.x_client.post(post.content, image_path)
            
            if result['success']:
                post.status = 'posted'
                post.post_id = result['post_id']
                db.session.commit()
                
                # Prepare notification message
                notification_message = f"""
Post ID: {post.id}
Content: {post.content}
Platform ID: {post.post_id}
Time: {datetime.utcnow().isoformat()}
"""
                # Add image info if applicable
                if image_path:
                    notification_message += f"Image: {post.image_filename}\n"
                if 'warning' in result:
                    notification_message += f"Warning: {result['warning']}\n"
                
                self.notifier.send_notification(
                    subject="Post Successfully Published",
                    message=notification_message
                )
            else:
                post.status = 'failed'
                db.session.commit()
                
                self.notifier.send_notification(
                    subject="Post Failed",
                    message=f"""
Post ID: {post.id}
Content: {post.content}
Error: {result.get('error', 'Unknown error')}
Time: {datetime.utcnow().isoformat()}
"""
                )
                
        except Exception as e:
            logger.error(f"Error processing post {post.id}: {str(e)}")
            self.notifier.send_notification(
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
    
    # Start scheduler
    scheduler = PostScheduler()
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