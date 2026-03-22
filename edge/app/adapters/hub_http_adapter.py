import logging
import requests
import json
from app.interfaces.hub_gateway import HubGateway
from app.entities.processed_agent_data import ProcessedAgentData

class HubHttpAdapter(HubGateway):
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def save_data(self, processed_data: ProcessedAgentData) -> bool:
        url = f"{self.api_base_url}/processed_agent_data/"
        
        try:
            if hasattr(processed_data, "model_dump"):
                data = processed_data.model_dump()
            elif hasattr(processed_data, "dict"):
                data = processed_data.dict()
            else:
                data = processed_data.__dict__

            self.logger.info(f"Sending data to Hub (HTTP): {data}")

            json_payload = json.dumps(data, default=str)

            response = requests.post(
                url, 
                data=json_payload, 
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200 or response.status_code == 201:
                self.logger.info("Data successfully sent to Hub via HTTP.")
                return True
            else:
                self.logger.error(f"Failed to send data via HTTP. Status: {response.status_code}, Response: {response.text}")
                return False

        except requests.exceptions.ConnectionError:
            self.logger.error(f"Connection error: Could not connect to {url}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error in HubHttpAdapter: {e}")
            return False