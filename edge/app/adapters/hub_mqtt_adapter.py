import logging
import json
import paho.mqtt.client as mqtt
from typing import Any

from app.interfaces.hub_gateway import HubGateway
from app.entities.processed_agent_data import ProcessedAgentData

class HubMqttAdapter(HubGateway):
    def __init__(self, broker: str, port: int, topic: str):
        self.broker = broker
        self.port = port
        self.topic = topic
        
        self.client = mqtt.Client()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self._connect()

    def _connect(self):
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()  # Запускаємо в окремому потоці для обробки мережевих подій
            self.logger.info(f"Connected to Hub MQTT Broker at {self.broker}:{self.port}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Hub MQTT Broker: {e}")

    def save_data(self, processed_data: ProcessedAgentData) -> bool:
        try:
            if hasattr(processed_data, "model_dump_json"):
                payload = processed_data.model_dump_json()
            elif hasattr(processed_data, "json") and callable(processed_data.json):
                 payload = processed_data.json()
            elif hasattr(processed_data, "__dict__"):
                payload = json.dumps(processed_data.__dict__, default=str)
            else:
                payload = json.dumps(processed_data, default=str)

            msg_info = self.client.publish(self.topic, payload, qos=1)
            
            msg_info.wait_for_publish(timeout=2.0)

            if msg_info.is_published():
                self.logger.debug(f"Successfully published data to {self.topic}")
                return True
            else:
                self.logger.warning("Message publication timed out or failed.")
                return False

        except Exception as e:
            self.logger.error(f"Error saving data to Hub: {e}")
            return False

    def __del__(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except:
            pass