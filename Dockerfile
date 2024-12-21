FROM python:3.11-slim

# Install necessary system packages
RUN apt-get update && apt-get install -y \
    libolm3 libolm-dev build-essential cmake

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot script and any other necessary files
COPY reaction_bot.py .

# Set environment variables (optional: consider using Docker secrets or environment files)
ENV HOMESERVER_URL="HOMESERVER_URL"
ENV BOT_USERNAME="BOT_USERNAME"
ENV BOT_PASSWORD="BOT_PASSWORD"
ENV WEBHOOK_URL="WEBHOOK_URL"

# Expose any ports if necessary (not needed for this bot)

# Run the bot
CMD ["python", "reaction_bot.py"]
