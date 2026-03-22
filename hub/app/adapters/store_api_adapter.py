import json
import logging
from typing import List
import requests
from app.entities.processed_agent_data import ProcessedAgentData
from app.interfaces.store_api_gateway import StoreGateway

class StoreApiAdapter(StoreGateway):
    def __init__(self, api_base_url):
        self.api_base_url = api_base_url

    def save_data(self, processed_agent_data_batch: List[ProcessedAgentData]) -> bool:
        """
        Відправляє батч оброблених даних до Store API.
        """
        endpoint = f"{self.api_base_url}/processed_agent_data"

        payload = [item.model_dump(mode='json') for item in processed_agent_data_batch]

        try:
            response = requests.post(endpoint, json=payload)

            if response.status_code == 200 or response.status_code == 201:
                logging.info(f"Successfully saved {len(processed_agent_data_batch)} records via Store API.")
                return True
            else:
                logging.error(f"Failed to save data. Status: {response.status_code}. Response: {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error while connecting to Store API: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error in StoreApiAdapter: {e}")
            return False