# MongoDB Backup Solution

This solution provides automated MongoDB backups that run daily at midnight. It keeps backups for the last 14 days and automatically removes older backups.

## Features

- Daily automated backups at midnight
- Retains the last 14 days of backups
- Automatically removes backups older than 14 days
- Each backup is stored in a date-named folder (YYYY-MM-DD format)
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

### 3. Configure the MongoDB connection

Copy the `.env.example` file to `.env` and update the MongoDB connection string:

```bash
cp .env.example .env
```

Edit the `.env` file to set your MongoDB connection string:

```
MONGODB_URI=mongodb://username:password@mongodb:27017/database
```

### 4. Build and start the backup container

```bash
docker-compose up -d
```

This will:
- Build the Docker image
- Start the backup container
- Configure the cron job to run daily at midnight

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
mongorestore --uri="your_mongodb_uri" backups/YYYY-MM-DD/
```

Replace `YYYY-MM-DD` with the date of the backup you want to restore.

## Customization

You can modify the following parameters:

### Number of days to keep backups

Edit the `DAYS_TO_KEEP` variable in the `mongodb_backup.py` script:

```python
DAYS_TO_KEEP = 14  # Change to your desired number of days
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

3. Verify that the MongoDB connection string is correct in your `.env` file

### Backups are not visible in the local directory

Make sure the directory permissions allow the container to write to the `backups` folder:

```bash
sudo chown -R 1000:1000 backups/
```

### Cron is not running the backup

You can verify if cron is working by checking the cron logs inside the container:

```bash
docker-compose exec mongodb-backup grep CRON /var/log/syslog
```