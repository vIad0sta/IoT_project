import logging
import json
import paho.mqtt.client as mqtt
from typing import Any

from app.interfaces.agent_gateway import AgentGateway
from app.interfaces.hub_gateway import HubGateway
from app.entities.agent_data import AgentData
from app.usercases.data_processing import process_agent_data

class AgentMQTTAdapter(AgentGateway):
    def __init__(
        self,
        broker_host: str,
        broker_port: int,
        topic: str,
        hub_gateway: HubGateway,
        batch_size: int = 10
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = topic
        self.hub_gateway = hub_gateway
        
        self.client = mqtt.Client()
        
        self.client.on_connect = self._on_connect
        self.client.on_message = self.on_message
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info(f"Connected to MQTT Broker at {self.broker_host}:{self.broker_port}")
            client.subscribe(self.topic)
            self.logger.info(f"Subscribed to topic: {self.topic}")
        else:
            self.logger.error(f"Failed to connect, return code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
            self.logger.debug(f"Received message: {payload}")
            
            data_dict = json.loads(payload)
            
            try:
                agent_data = AgentData(**data_dict) 
            except Exception as e:
                self.logger.error(f"Error parsing AgentData: {e}")
                return

            processed_data = process_agent_data(agent_data)
            
            if self.hub_gateway.save_data(processed_data):
                self.logger.info(f"Data processed and sent to Hub. State: {processed_data.road_state}")
            else:
                self.logger.warning("Failed to send data to Hub")

        except json.JSONDecodeError:
            self.logger.error("Failed to decode JSON payload")
        except Exception as e:
            self.logger.error(f"Unexpected error in on_message: {e}")

    def connect(self):
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            raise e

    def start(self):
        self.client.loop_start()
        self.logger.info("MQTT loop started")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
        self.logger.info("MQTT adapter stopped")