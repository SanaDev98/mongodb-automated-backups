#!/usr/bin/env python3
import os
import sys
import time
import shutil
import logging
import datetime
from subprocess import run, PIPE, CalledProcessError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/mongodb-backup.log')
    ]
)
logger = logging.getLogger('mongodb-backup')

# Configuration
BACKUP_DIR = "/backups"
DAYS_TO_KEEP = 14
MONGODB_URI = os.environ.get('MONGODB_URI')

if not MONGODB_URI:
    logger.error("MONGODB_URI environment variable is not set")
    sys.exit(1)

def create_backup():
    """Create MongoDB backup using mongodump"""
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    backup_path = os.path.join(BACKUP_DIR, current_date)
    
    # Create backup directory if it doesn't exist
    if not os.path.exists(backup_path):
        os.makedirs(backup_path)
    
    logger.info(f"Starting MongoDB backup to {backup_path}")
    
    try:
        # Run mongodump command
        result = run([
            'mongodump',
            '--uri', MONGODB_URI,
            '--out', backup_path
        ], check=True, stderr=PIPE)
        
        logger.info("MongoDB backup completed successfully")
        return True
    except CalledProcessError as e:
        logger.error(f"MongoDB backup failed: {e.stderr.decode()}")
        return False

def cleanup_old_backups():
    """Delete backups older than DAYS_TO_KEEP days"""
    logger.info(f"Cleaning up backups older than {DAYS_TO_KEEP} days")
    
    # Get all backup directories
    backup_dirs = []
    for item in os.listdir(BACKUP_DIR):
        item_path = os.path.join(BACKUP_DIR, item)
        if os.path.isdir(item_path) and is_date_format(item):
            backup_dirs.append(item)
    
    # Sort backup directories by date (oldest first)
    backup_dirs.sort()
    
    # Remove oldest backups if we have more than DAYS_TO_KEEP
    while len(backup_dirs) > DAYS_TO_KEEP:
        oldest_backup = backup_dirs.pop(0)
        oldest_backup_path = os.path.join(BACKUP_DIR, oldest_backup)
        
        logger.info(f"Removing old backup: {oldest_backup}")
        try:
            shutil.rmtree(oldest_backup_path)
        except Exception as e:
            logger.error(f"Failed to remove old backup {oldest_backup}: {e}")

def is_date_format(dirname):
    """Check if directory name matches date format YYYY-MM-DD"""
    try:
        datetime.datetime.strptime(dirname, "%Y-%m-%d")
        return True
    except ValueError:
        return False

if __name__ == "__main__":
    # Ensure backup directory exists
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    # Create backup
    backup_success = create_backup()
    
    # Cleanup old backups only if the current backup was successful
    if backup_success:
        cleanup_old_backups()
