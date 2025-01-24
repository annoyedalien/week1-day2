import os
import json
import urllib.request
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import logging

import azure.functions as func

app = func.FunctionApp()

# Load environment variables from .env file
load_dotenv()

@app.timer_trigger(schedule="30 * * * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:
    
    if myTimer.past_due:
        logging.info('The timer is past due!')

    #logging.info('Python timer trigger function executed.')

    def format_game_data(game):
        status = game.get("Status", "Unknown")
        away_team = game.get("AwayTeam", "Unknown")
        home_team = game.get("HomeTeam", "Unknown")
        final_score = f"{game.get('AwayTeamScore', 'N/A')}-{game.get('HomeTeamScore', 'N/A')}"
        start_time = game.get("DateTime", "Unknown")
        channel = game.get("Channel", "Unknown")
        
        # Format quarters
        quarters = game.get("Quarters", [])
        quarter_scores = ', '.join([f"Q{q['Number']}: {q.get('AwayScore', 'N/A')}-{q.get('HomeScore', 'N/A')}" for q in quarters])
        
        if status == "Final":
            return (
                f"Game Status: {status}\n"
                f"{away_team} vs {home_team}\n"
                f"Final Score: {final_score}\n"
                f"Start Time: {start_time}\n"
                f"Channel: {channel}\n"
                f"Quarter Scores: {quarter_scores}\n"
            )
        elif status == "InProgress":
            last_play = game.get("LastPlay", "N/A")
            return (
                f"Game Status: {status}\n"
                f"{away_team} vs {home_team}\n"
                f"Current Score: {final_score}\n"
                f"Last Play: {last_play}\n"
                f"Channel: {channel}\n"
            )
        elif status == "Scheduled":
            return (
                f"Game Status: {status}\n"
                f"{away_team} vs {home_team}\n"
                f"Start Time: {start_time}\n"
                f"Channel: {channel}\n"
            )
        else:
            return (
                f"Game Status: {status}\n"
                f"{away_team} vs {home_team}\n"
                f"Details are unavailable at the moment.\n"
            )

    # Get environment variables
    api_key = os.getenv("NBA_API_KEY")
    connection_str = os.getenv("SERVICE_BUS_CONNECTION_STR")
    topic_name = os.getenv("SERVICE_BUS_TOPIC_NAME")

    # Adjust for Central Time (UTC-6)
    utc_now = datetime.now(timezone.utc)
    central_time = utc_now - timedelta(hours=6)  # Central Time is UTC-6
    today_date = central_time.strftime("%Y-%m-%d")

    logging.info(f"Fetching games for date: {today_date}")

    # Fetch data from the API
    api_url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{today_date}?key={api_key}"
    logging.info(today_date)

    try:
        with urllib.request.urlopen(api_url) as response:
            data = json.loads(response.read().decode())
            logging.info(json.dumps(data, indent=4))  # Debugging: log the raw data
    except Exception as e:
        logging.error(f"Error fetching data from API: {e}")

    # Include all games (final, in-progress, and scheduled)
    messages = [format_game_data(game) for game in data]
    final_message = "\n---\n".join(messages) if messages else "No games available for today."

    # Send the message to the Service Bus topic
    try:
        servicebus_client = ServiceBusClient.from_connection_string(conn_str=connection_str, logging_enable=True)
        with servicebus_client:
            sender = servicebus_client.get_topic_sender(topic_name=topic_name)
            with sender:
                message = ServiceBusMessage(final_message)
                sender.send_messages(message)
                logging.info("Message sent to the topic.")
    except Exception as e:
        logging.error(f"Error sending message to Service Bus topic: {e}")