from langchain_core.tools import tool
from  dotenv import load_dotenv
import os
import requests
import logging
import asyncio
from requests import post
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
logger = logging.getLogger(__name__)


@tool
def ha_get_entities_containing(filter: str) -> list:
    """
    Retrieve all entity names from Home Assistant and filter the ones that contain the specified value.

    Args:
        filter: A string to filter the entity names by using the __contains__() method.

    Returns:
        list: A list of entity names that contain the specified value.
    """
    # Load environment variables (for HA_TOKEN)
    load_dotenv()
    token = os.getenv('HA_TOKEN')

    # Define headers for the API request
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # API URL to retrieve all entity states from Home Assistant
    api_url = "http://192.168.86.12:8123/api/states"

    # Make a GET request to Home Assistant API
    response = requests.get(api_url, headers=headers)
    print(f"[TOOL][Api call] => ha_get_entities_containing({filter})")
    # Check if the response is successful
    if response.status_code == 200:
        # Parse the JSON response
        entities = response.json()
        # Initialize an empty list to hold filtered entity names
        filtered_entities = []

        # Loop through the list of entities
        for entity in entities:
            entity_id = entity.get('entity_id')

            # Add the entity_id to the list if it contains the specified value
            if filter in entity_id:
                filtered_entities.append(entity_id)

        return filtered_entities
    else:
        logger.critical(f"'ha_get_entities_containing' API call failed to Home Assistant with URL: {api_url}, Status Code: {response.status_code}")
        return []
@tool
def ha_get_state_of_a_specific_entity(entity_id) -> dict:
    """
    Retrieves the current state of a specific entity from the Home Assistant API.

    Args:
        entity_id (str): The entity ID of the sensor in Home Assistant (e.g., 'zone.neda').

    Returns:
        dict: A dictionary containing the state information of the specified sensor, or an empty dictionary if the API call fails.

    Raises:
        Critical: Logs a critical message if the API call to Home Assistant fails.
    """
    print(f"[TOOL][Api call] => get_state_of_specific_entity({entity_id})")
    # Load environment variables, including the Home Assistant token
    load_dotenv()

    # Get the Home Assistant token from environment variables
    token = os.getenv('HA_TOKEN')

    # Define the request headers with authorization and content type
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Construct the API URL using the provided entity_id
    api_url = f"http://192.168.86.12:8123/api/states/{entity_id}"

    # Make a GET request to the Home Assistant API to retrieve the sensor state
    response = requests.get(api_url, headers=headers)

    # If the API call is successful, return the response as a JSON object
    if response.status_code == 200:
        result = response.json()
        return result
    else:
        # Log a critical error if the API call fails and return an empty dictionary
        logger.critical(
            f"ha_get_state_of_a_specific_sensor(entity_id) API call failed to Home Assistant with URL: {api_url}, Status Code: {response.status_code}")
        return {}
@tool
def ha_set_state_of_a_specific_entity(entity_id,data) -> dict:
    """
    Unfinished Function
    """
    print(f"[TOOL][Api call] => set_state_of_specific_entity({entity_id})")
    # Load environment variables, including the Home Assistant token
    load_dotenv()
    # Get the Home Assistant token from environment variables
    token = os.getenv('HA_TOKEN')
    # Define the request headers with authorization and content type
    headers = {"Authorization": f"Bearer {token}","Content-Type": "application/json"}
    # Construct the API URL using the provided entity_id
    api_url = f"http://192.168.86.12:8123/api/states/{entity_id}"
    response = post(api_url, headers=headers, json=data)
    # If the API call is successful, return the response as a JSON object
    if response.status_code == 200:
        result = response.json()
        return result
    else:
        # Log a critical error if the API call fails and return an empty dictionary
        logger.critical(
            f"ha_get_state_of_a_specific_sensor(entity_id) API call failed to Home Assistant with URL: {api_url}, Status Code: {response.status_code}")
        return {}
@tool
def ha_get_entity_history(entity_id):
    """
    Fetches the past 10 days of state history for the specified Home Assistant entity.

    Parameters:
    -----------
    entity_id : str
        The unique ID of the Home Assistant entity to retrieve history for.

    Returns:
    --------
    list of dict or None
        A list of dictionaries with each entry containing:
        - 'state': str - The entity's state at a specific time.
        - 'when': str - The timestamp of the state change.
        Returns None if the request fails.
    """
    print(f"[TOOL][Api call] => get_history_of_a_specific_entity({entity_id})")
    try:
        # Load environment variables
        load_dotenv()
        token = os.getenv('HA_TOKEN')
        
        # Use correct port 8123 for Home Assistant
        ha_url = "http://192.168.86.12:8123"
        
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # Calculate dates properly (from 10 days ago until now)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=10)
        
        # Format dates properly for the API
        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        api_url = f"{ha_url}/api/history/period/{start_time_str}?filter_entity_id={entity_id}&end_time={end_time_str}&no_attributes"
        print(f"Requesting: {api_url}")

        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            compacted_data = []
            for record_group in result:
                for record in record_group:
                    compacted_data.append({
                        'state': record['state'],
                        'when': record['last_changed']
                    })
            if len(compacted_data) > 100:
                return compacted_data[-100:]
            return compacted_data or []  # Return empty list instead of None if no data
        else:
            logger.error(f"API call failed with status code: {response.status_code}")
            return []
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error occurred: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
        return []
@tool
def ha_get_logbook(entity_id=None, days=0.1):
    """
    Fetches logbook records for a specified Home Assistant entity or all entities within a given timeframe.

    Parameters:
    -----------
    entity_id : str, optional
        The unique ID of the Home Assistant entity to retrieve logs for. If None, retrieves logs for all entities.
    days : int, optional
        Number of past days to include in the log records. Default is 0.1.

    Returns:
    --------
    list of dict or None
        A list of dictionaries, each containing:
            - 'name': str - The entity's friendly name or event name.
            - 'message': str - A description of the event.
            - 'when': str - The timestamp of the log entry.
        Returns None if the request fails.
    """
    print(f"[TOOL][Api call] => ha_get_logbook(entitiy_id:{entity_id}, days:{days})")
    load_dotenv()
    token = os.getenv('HA_TOKEN')
    ha_url = os.getenv('HA_URL')

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Construct time range for logs
    start_time = (datetime.now() - timedelta(days=days)).isoformat(timespec='seconds') + 'Z'
    api_url = f"{ha_url}/api/logbook/{start_time}"

    # Include entity_id filter if provided
    if entity_id:
        api_url += f"?entity={entity_id}"

    response = requests.get(api_url, headers=headers)

    # Process the response
    if response.status_code == 200:
        log_data = response.json()
        compacted_logs = []
        for log in log_data:
            compacted_logs.append({
                'name': log.get('name')
                ,'state': log.get('state')
                ,'message': log.get('message')
                ,'when': log.get('when')
            })
        return compacted_logs
    else:
        logger.critical(
            f"ha_get_logbook() API call failed to Home Assistant with URL: {api_url}, Status Code: {response.status_code}")
        return None

async def main():
    print("Home Assistant Tools Testing Interface")
    print("Available commands:")
    print("1: Test ha_get_entities_containing")
    print("2: Test ha_get_state_of_a_specific_entity")
    print("3: Test ha_get_entity_history")
    print("4: Test ha_get_logbook")
    print("q: Quit")

    while True:
        choice = input("\nEnter command (1-4, q to quit): ")
        
        if choice == 'q':
            break
            
        if choice == '1':
            filter_text = input("Enter filter text: ")
            result = ha_get_entities_containing(filter_text)
            print("\nResults:")
            for entity in result:
                print(f"- {entity}")
                
        elif choice == '2':
            entity_id= input("Enter entity ID: ")
            result = ha_get_state_of_a_specific_entity(entity_id)
            print("\nResult:", json.dumps(result, indent=2))
            
        elif choice == '3':
            entity_id = input("Enter entity ID: ")
            result = ha_get_entity_history(entity_id)
            print("\nLast 5 history entries:")
            if not result:
                print("No history data available")
            else:
                for entry in result[:5]:  # Show only last 5 entries
                    print(f"State: {entry['state']}, When: {entry['when']}")
        elif choice == '4':
            entity_id = input("Enter entity ID (press Enter for all entities): ") or None
            days = float(input("Enter number of days (default 0.1): ") or "0.1")
            result = ha_get_logbook(entity_id, days)
            print("\nLast 5 log entries:")
            for entry in result:  # Show only last 5 entries
                print(f"Name: {entry['name']}, State: {entry['state']}, When: {entry['when']}")
                print(f"Message: {entry['message']}\n")

if __name__ == "__main__":
    asyncio.run(main())