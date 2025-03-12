"""
Fore-Poster Notification System

This module provides notification capabilities for Fore-Poster, primarily email alerts
using AWS SES in production and logging in development environments.

Usage:
    from core.notification import get_notifier
    
    notifier = get_notifier()
    notifier.send_notification(
        subject="Notification Subject", 
        message="Notification message content"
    )
"""
import logging
from datetime import datetime
from config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('notification.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global notifier instance
_notifier = None

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

def init_notifier():
    """Initialize or reinitialize the global notifier instance.
    This should be called after Config has been initialized."""
    global _notifier
    _notifier = NotificationHandler()
    return _notifier

def get_notifier():
    """Get the global notifier instance, initializing it if needed."""
    global _notifier
    if _notifier is None:
        _notifier = NotificationHandler()
    return _notifier

# Backward compatibility - Create a default instance that will be reinitialized later
notifier = NotificationHandler() 