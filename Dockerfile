FROM python:3.11-slim

# Install MongoDB tools
RUN apt-get update && \
    apt-get install -y gnupg curl && \
    curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
    gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor && \
    echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] http://repo.mongodb.org/apt/debian bullseye/mongodb-org/7.0 main" | \
    tee /etc/apt/sources.list.d/mongodb-org-7.0.list && \
    apt-get update && \
    apt-get install -y mongodb-database-tools && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create backup directory
RUN mkdir -p /backups /var/log

# Copy backup script
COPY mongodb_backup.py /usr/local/bin/
RUN chmod +x /usr/local/bin/mongodb_backup.py

# Create a cron job to run backup at midnight every day
RUN apt-get update && \
    apt-get install -y cron && \
    echo "0 0 * * * /usr/local/bin/mongodb_backup.py" > /etc/cron.d/mongodb-backup && \
    chmod 0644 /etc/cron.d/mongodb-backup && \
    crontab /etc/cron.d/mongodb-backup

# Create entrypoint script
RUN echo '#!/bin/sh\n\
# Start cron in the background\n\
cron\n\
\n\
# Run initial backup if requested\n\
if [ "$INITIAL_BACKUP" = "true" ]; then\n\
    echo "Running initial backup..."\n\
    /usr/local/bin/mongodb_backup.py\n\
fi\n\
\n\
# Keep container running\n\
tail -f /var/log/mongodb-backup.log\n' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

VOLUME ["/backups"]

# Run the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]