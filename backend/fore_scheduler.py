from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from sqlalchemy import and_
from fore_poster import app, db, Post, XClient
from config import Config
import boto3
import logging
import time
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NotificationHandler:
    def __init__(self):
        self.production = Config.PRODUCTION
        if self.production:
            self.ses = boto3.client('ses', region_name=Config.AWS_REGION)
            self.sender = Config.SES_SENDER
            self.recipient = Config.SES_RECIPIENT

    def send_notification(self, subject: str, message: str):
        if not self.production:
            logger.info(f"Development mode - would send email: {subject}")
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
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.x_client = XClient()
        self.notifier = NotificationHandler()
        
    def start(self):
        self.scheduler.add_job(
            func=self.check_scheduled_posts,
            trigger=IntervalTrigger(minutes=1),
            id='check_posts',
            name='Check scheduled posts'
        )
        self.scheduler.start()
        logger.info("Scheduler started")
        
    def check_scheduled_posts(self):
        with app.app_context():
            now = datetime.utcnow()
            upcoming = now + timedelta(minutes=1)
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
        try:
            result = self.x_client.post(post.content)
            
            if result['success']:
                post.status = 'posted'
                post.post_id = result['post_id']
                db.session.commit()
                
                self.notifier.send_notification(
                    subject="Post Successfully Published",
                    message=f"""
Post ID: {post.id}
Content: {post.content}
Platform ID: {post.post_id}
Time: {datetime.utcnow().isoformat()}
                    """
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

if __name__ == "__main__":
    Config.init_app(os.getenv('FLASK_DEBUG', 'development'))
    scheduler = PostScheduler()
    scheduler.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.scheduler.shutdown()