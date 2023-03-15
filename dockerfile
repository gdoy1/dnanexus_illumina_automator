FROM python:3.8

# Set environment variables
ENV PROJECT=/home/bioinf/george/pipeline_automation/
ENV VENV_PATH=/home/bioinf/george/pipeline_automation/myenv
ENV RUN_DIRECTORY=/home/bioinf/george/pipeline_automation/*/*/*/

# Install any necessary packages
RUN apt-get update && apt-get install -y cron

# Create a new cron job file and add the monitor.sh command
RUN echo '* * * * * /bin/bash /path/to/monitor.sh >> /var/log/monitor.log 2>&1' > /etc/cron.d/monitor-cron

# Give execute permission to the cron job file
RUN chmod 0644 /etc/cron.d/monitor-cron

# Add the rest of the project files
ADD . /path/to/project

# Start cron service
CMD cron && tail -f /var/log/monitor.log