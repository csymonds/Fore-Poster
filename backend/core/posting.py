"""
Fore-Poster Posting Service

This module provides common functionality for posting to social media platforms.
It centralizes the posting logic used by both fore_poster.py and fore_scheduler.py.

Usage:
    from core.posting import post_to_platform
    
    result = post_to_platform(post, client, image_path)
"""
import logging
import os
from datetime import datetime
from core.notification import get_notifier

# Set up logging
logger = logging.getLogger(__name__)

def post_to_platform(post, client, image_path=None):
    """
    Post content to a social media platform and send notifications.
    
    This function centralizes the posting logic and notification handling to ensure
    consistent behavior between immediate and scheduled posts.
    
    Args:
        post: The Post object to be posted
        client: The social media client to use (e.g., XClient)
        image_path: Optional path to an image file
        
    Returns:
        dict: Result information including success status, post_id, and any errors/warnings
    """
    logger.info(f"Processing post for ID: {post.id}")
    
    # Get the current notifier instance
    notifier = get_notifier()
    
    if post.platform != 'x':
        logger.error(f"Unsupported platform: {post.platform}")
        return {'success': False, 'error': f'Unsupported platform: {post.platform}'}
    
    # Check if image exists if specified
    if image_path and not os.path.exists(image_path):
        logger.warning(f"Image file not found: {image_path}")
        image_path = None
    elif image_path:
        logger.info(f"Including image: {os.path.basename(image_path)}")
    
    # Post with or without image
    try:
        result = client.post(post.content, image_path)
        
        if result['success']:
            # Prepare notification message
            notification_message = f"""
Post ID: {post.id}
Content: {post.content}
Platform ID: {result['post_id']}
Time: {datetime.utcnow().isoformat()}
"""
            # Add image info if applicable
            if image_path:
                notification_message += f"Image: {os.path.basename(image_path)}\n"
            if 'warning' in result:
                notification_message += f"Warning: {result['warning']}\n"
            
            # Add full API response to the message
            notification_message += f"\nAPI Response: {result}\n"
            
            # Send notification
            notifier.send_notification(
                subject="Post Successfully Published",
                message=notification_message
            )
            
            return result
        else:
            # Send failure notification
            notifier.send_notification(
                subject="Post Failed",
                message=f"""
Post ID: {post.id}
Content: {post.content}
Error: {result.get('error', 'Unknown error')}
Time: {datetime.utcnow().isoformat()}

API Response: {result}
"""
            )
            
            return result
            
    except Exception as e:
        error_message = f"Error processing post {post.id}: {str(e)}"
        logger.error(error_message)
        
        # Send error notification
        notifier.send_notification(
            subject="Posting Error",
            message=f"""
Post ID: {post.id}
Content: {post.content}
Error: {str(e)}
Time: {datetime.utcnow().isoformat()}
"""
        )
        
        return {'success': False, 'error': error_message} 