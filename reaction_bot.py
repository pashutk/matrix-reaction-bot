import asyncio
import os
import requests
import logging
from nio import AsyncClient, MatrixRoom, LoginResponse
from nio.exceptions import LocalProtocolError
from nio.events.room_events import ReactionEvent  # Updated import

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Read configuration from environment variables
HOMESERVER_URL = os.getenv('HOMESERVER_URL')
USERNAME = os.getenv('BOT_USERNAME')
PASSWORD = os.getenv('BOT_PASSWORD')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Read the optional cutoff timestamp from environment variables
CUTOFF_TIMESTAMP = os.getenv('CUTOFF_TIMESTAMP')

# Validate configuration
if not all([HOMESERVER_URL, USERNAME, PASSWORD, WEBHOOK_URL]):
    logger.error("One or more environment variables are not set. Please set HOMESERVER_URL, BOT_USERNAME, BOT_PASSWORD, and WEBHOOK_URL.")
    exit(1)

# Convert the cutoff timestamp to an integer if provided
if CUTOFF_TIMESTAMP:
    try:
        CUTOFF_TIMESTAMP = int(CUTOFF_TIMESTAMP)
        logger.info(f"Using cutoff timestamp: {CUTOFF_TIMESTAMP}")
    except ValueError:
        logger.error("CUTOFF_TIMESTAMP must be an integer representing milliseconds since epoch.")
        exit(1)
else:
    logger.info("No cutoff timestamp provided. Processing all events.")
    CUTOFF_TIMESTAMP = None  # Explicitly set to None for clarity

async def main():
    # Initialize the client
    client = AsyncClient(HOMESERVER_URL, USERNAME)

    try:
        # Log in and store the access token for future sessions
        response = await client.login(PASSWORD)
        if isinstance(response, LoginResponse):
            logger.info("Logged in successfully")
        else:
            logger.error(f"Failed to login: {response}")
            return

        # Define a callback for reaction events
        async def reaction_callback(room: MatrixRoom, event: ReactionEvent):
            # Ignore reactions from ourselves
            if event.sender == client.user_id:
                return

            if CUTOFF_TIMESTAMP and event.server_timestamp < CUTOFF_TIMESTAMP:
                logger.debug(f"Ignoring event {event.event_id} from {event.sender} as it occurred before the cutoff timestamp.")
                return

            # Extract the event ID of the reaction and the message being reacted to
            reaction_event_id = event.event_id  # The event ID of the reaction itself
            reacted_event_id = event.reacts_to  # The event ID of the original message
            reaction_key = event.key  # The reaction itself (e.g., an emoji)

            logger.info(f"Reaction detected in room '{room.display_name}' from {event.sender}")
            logger.debug(f"Reaction event ID: {reaction_event_id}")
            logger.debug(f"Reacted to event ID: {reacted_event_id}")
            logger.debug(f"Reaction key: {reaction_key}")

            # Prepare data to send to the webhook
            data = {
                "room_id": room.room_id,
                "room_name": room.display_name,
                "sender": event.sender,
                "reaction_event_id": reaction_event_id,
                "reacted_event_id": reacted_event_id,
                "reaction": reaction_key,
            }

            # Send the data to the webhook
            try:
                webhook_response = requests.post(WEBHOOK_URL, json=data)
                webhook_response.raise_for_status()
                logger.info("Webhook request sent successfully")
            except requests.RequestException as e:
                logger.error(f"Failed to send webhook request: {e}")

        # Add the callback to the client for reaction events
        client.add_event_callback(reaction_callback, ReactionEvent)

        # Start syncing with the server
        await client.sync_forever(timeout=30000)  # Sync every 30 seconds

    except LocalProtocolError as e:
        logger.error(f"Matrix protocol error: {e}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())