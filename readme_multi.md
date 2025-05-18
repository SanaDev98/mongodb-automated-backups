# MongoDB Multi-Instance Backup Solution

This solution provides automated backups for multiple MongoDB instances (separate servers/deployments) that run daily at midnight. It keeps backups for a configurable number of days (default 14) and automatically removes older backups.

## Features

- Support for multiple MongoDB instances with separate connection strings
- Each instance is backed up completely (all databases within that instance)
- Daily automated backups at midnight
- Configurable retention period (default 14 days)
- Automatically removes backups older than the retention period
- Each backup is stored in a date-named folder (YYYY-MM-DD format) within instance-specific directories
- Logs backup operations for monitoring
- Runs in Docker for easy deployment
- Backups are stored in a local directory for easy access

## Setup Instructions

### 1. Create the configuration files

You need the following files in the same directory:
- `mongodb_backup.py` - Python script for backup and cleanup
- `Dockerfile` - Docker container configuration
- `docker-compose.yml` - Docker Compose configuration
- `.env` - Environment variables configuration

### 2. Create a local backup directory

```bash
mkdir -p backups
```

This directory will store all your MongoDB backups.

### 3. Configure the MongoDB connections

Copy the `.env.example` file to `.env`:

```bash
cp .env.example .env
```

Edit the `.env` file to set your MongoDB connection strings. You have three options:

#### Option 1: Configure multiple MongoDB instances separately

```
# Production MongoDB instance
MONGODB_URI_PRODUCTION=mongodb://username:password@production-mongodb:27017/

# Staging MongoDB instance
MONGODB_URI_STAGING=mongodb://username:password@staging-mongodb:27017/

# Development MongoDB instance
MONGODB_URI_DEVELOPMENT=mongodb://username:password@dev-mongodb:27017/
```

The format is `MONGODB_URI_[INSTANCE_NAME]` where `[INSTANCE_NAME]` becomes the subdirectory where backups are stored.

#### Option 2: Configure with JSON

```
MONGODB_CONNECTIONS='{"analytics": "mongodb://username:password@analytics-mongodb:27017/", "reporting": "mongodb://username:password@reporting-mongodb:27017/"}'
```

#### Option 3: Single instance (backward compatibility)

```
MONGODB_URI=mongodb://username:password@mongodb:27017/
```

You can also set the number of days to keep backups:

```
DAYS_TO_KEEP=30
```

### 4. Build and start the backup container

```bash
docker-compose up -d
```

This will:
- Build the Docker image
- Start the backup container
- Configure the cron job to run daily at midnight

## Backup Structure

Backups are organized by MongoDB instance name and date:

```
backups/
  ├── production/
  │   ├── 2025-05-15/
  │   └── 2025-05-16/
  ├── staging/
  │   ├── 2025-05-15/
  │   └── 2025-05-16/
  └── development/
      ├── 2025-05-15/
      └── 2025-05-16/
```

Each date directory contains a complete backup of all databases in that MongoDB instance.

## Monitoring Backups

You can check the logs of the backup process:

```bash
docker-compose logs mongodb-backup
```

To see the created backups:

```bash
ls -la backups/
```

## Manual Backup

If you want to run a backup immediately, you can either:

1. Set `INITIAL_BACKUP=true` in the `.env` file before starting the container, or

2. Run a manual backup command:
```bash
docker-compose exec mongodb-backup /usr/local/bin/mongodb_backup.py
```

## Restoring from Backup

To restore from a backup, you can use the `mongorestore` command:

```bash
# Restore a complete MongoDB instance
mongorestore --uri="mongodb://username:password@host:port/" backups/[instance-name]/YYYY-MM-DD/

# Restore a specific database from the backup
mongorestore --uri="mongodb://username:password@host:port/" --nsInclude="database.*" backups/[instance-name]/YYYY-MM-DD/
```

Replace `[instance-name]` with the name of the MongoDB instance and `YYYY-MM-DD` with the date of the backup you want to restore.

## Customization

You can modify the following parameters:

### Number of days to keep backups

Edit the `DAYS_TO_KEEP` variable in the `.env` file:

```
DAYS_TO_KEEP=30  # Change to your desired number of days
```

### Backup schedule

Change the cron schedule in the Dockerfile:

```dockerfile
# Default is midnight (0 0 * * *)
# For example, to run at 2 AM:
echo "0 2 * * * /usr/local/bin/mongodb_backup.py" > /etc/cron.d/mongodb-backup
```

### Backup location

The backups are stored in the `./backups` directory. You can change this by modifying the volume configuration in `docker-compose.yml`:

```yaml
volumes:
  - /path/to/your/preferred/location:/backups
```

## Troubleshooting

### No backups are being created

1. Check if the container is running:
```bash
docker-compose ps
```

2. Check the logs for errors:
```bash
docker-compose logs mongodb-backup
```

3. Verify that the MongoDB connection strings are correct in your `.env` file

### Backups are not visible in the local directory

Make sure the directory permissions allow the container to write to the `backups` folder:

```bash
sudo chown -R 1000:1000 backups/
```

### Cron is not running the backup

You can verify if cron is working by checking the logs inside the container:

```bash
docker-compose exec mongodb-backup grep CRON /var/log/syslog
```