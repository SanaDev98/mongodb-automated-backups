#!/usr/bin/env python3
import os
import sys
import time
import json
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
DAYS_TO_KEEP = int(os.environ.get('DAYS_TO_KEEP', 14))

# Get MongoDB connection strings from environment
def get_mongodb_connections():
    """
    Parse MongoDB connections from environment variables
    Format can be either:
    1. A JSON string in MONGODB_CONNECTIONS env var
    2. Multiple MONGODB_URI_[name] environment variables
    """
    connections = {}
    
    # Method 1: Check for JSON config
    json_config = os.environ.get('MONGODB_CONNECTIONS')
    if json_config:
        try:
            connections = json.loads(json_config)
            return connections
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse MONGODB_CONNECTIONS JSON: {e}")
    
    # Method 2: Check for individual connection strings
    for key in os.environ:
        if key.startswith('MONGODB_URI_'):
            instance_name = key[len('MONGODB_URI_'):].lower()
            connections[instance_name] = os.environ[key]
    
    # Backward compatibility: also check for the original MONGODB_URI
    if not connections and os.environ.get('MONGODB_URI'):
        connections['default'] = os.environ.get('MONGODB_URI')
    
    return connections

def create_backup(instance_name, connection_string):
    """Create MongoDB backup using mongodump for a complete MongoDB instance"""
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Use instance name as subfolder
    instance_backup_dir = os.path.join(BACKUP_DIR, instance_name)
    if not os.path.exists(instance_backup_dir):
        os.makedirs(instance_backup_dir)
    
    backup_path = os.path.join(instance_backup_dir, current_date)
    
    # Create backup directory if it doesn't exist
    if not os.path.exists(backup_path):
        os.makedirs(backup_path)
    
    logger.info(f"Starting MongoDB backup for instance '{instance_name}' to {backup_path}")
    
    try:
        # Run mongodump command with the full connection string to backup the entire instance
        result = run([
            'mongodump',
            '--uri', connection_string,
            '--out', backup_path
        ], check=True, stderr=PIPE)
        
        logger.info(f"MongoDB backup for instance '{instance_name}' completed successfully")
        return True
    except CalledProcessError as e:
        logger.error(f"MongoDB backup for instance '{instance_name}' failed: {e.stderr.decode()}")
        return False

def cleanup_old_backups(instance_name):
    """Delete backups older than DAYS_TO_KEEP days for a specific MongoDB instance"""
    logger.info(f"Cleaning up backups older than {DAYS_TO_KEEP} days for instance '{instance_name}'")
    
    instance_backup_dir = os.path.join(BACKUP_DIR, instance_name)
    if not os.path.exists(instance_backup_dir):
        return
    
    # Get all backup directories
    backup_dirs = []
    for item in os.listdir(instance_backup_dir):
        item_path = os.path.join(instance_backup_dir, item)
        if os.path.isdir(item_path) and is_date_format(item):
            backup_dirs.append(item)
    
    # Sort backup directories by date (oldest first)
    backup_dirs.sort()
    
    # Remove oldest backups if we have more than DAYS_TO_KEEP
    while len(backup_dirs) > DAYS_TO_KEEP:
        oldest_backup = backup_dirs.pop(0)
        oldest_backup_path = os.path.join(instance_backup_dir, oldest_backup)
        
        logger.info(f"Removing old backup for instance '{instance_name}': {oldest_backup}")
        try:
            shutil.rmtree(oldest_backup_path)
        except Exception as e:
            logger.error(f"Failed to remove old backup {oldest_backup} for instance '{instance_name}': {e}")

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
    
    # Get all MongoDB connections
    connections = get_mongodb_connections()
    
    if not connections:
        logger.error("No MongoDB connections configured. Please set MONGODB_CONNECTIONS or MONGODB_URI_[name] environment variables.")
        sys.exit(1)
    
    logger.info(f"Found {len(connections)} MongoDB instances to backup")
    
    # Process each connection
    for instance_name, connection_string in connections.items():
        # Create backup
        backup_success = create_backup(instance_name, connection_string)
        
        # Cleanup old backups only if the current backup was successful
        if backup_success:
            cleanup_old_backups(instance_name)
