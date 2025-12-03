"""
Basic MQTT Connection to AWS IoT Core
- Connects with X.509 certificate authentication
- Subscribes to command topic
- Publishes test telemetry
- Demonstrates connection lifecycle

SETUP:
  pip install -r requirements.txt
  python basic_mqtt_client.py
"""

import json
import time
from pathlib import Path
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

# Get the script's directory for resolving relative paths
SCRIPT_DIR = Path(__file__).parent.resolve()

class CANGatewayMQTTClient:
    """Manages MQTT connection to AWS IoT Core"""
    
    def __init__(self, config_path: str):
        """
        Initialize MQTT client with AWS IoT configuration
        
        Args:
            config_path: Path to config JSON with endpoint, cert paths
        """
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.endpoint = config['endpoint']
        self.thing_name = config['thing_name']
        # Resolve cert paths relative to script directory if they are relative paths
        self.cert_path = str(SCRIPT_DIR / config['cert_path']) if not Path(config['cert_path']).is_absolute() else config['cert_path']
        self.key_path = str(SCRIPT_DIR / config['key_path']) if not Path(config['key_path']).is_absolute() else config['key_path']
        self.ca_path = str(SCRIPT_DIR / config['ca_path']) if not Path(config['ca_path']).is_absolute() else config['ca_path']
        # Use client ID that matches AWS IoT policy
        self.client_id = config.get('client_id', 'can-gateway')
        
        # Create MQTT client
        self.mqtt_client = AWSIoTMQTTClient(self.client_id)
        self.mqtt_client.configureEndpoint(self.endpoint, 8883)  # AWS IoT port
        
        # Configure certificates for mTLS
        self.mqtt_client.configureCredentials(
            self.ca_path,      # Root CA for TLS chain validation
            self.key_path,     # Device private key
            self.cert_path     # Device certificate
        )
        
        # Configure connection parameters
        self.mqtt_client.configureAutoReconnectBackoffTime(
            maxReconnectQuietTimeSecond=32,
            stableConnectionTimeSecond=20,
            baseReconnectQuietTimeSecond=1
        )
        self.mqtt_client.configureOfflinePublishQueueing(-1)  # Unlimited queue
        self.mqtt_client.configureDrainingFrequency(2)  # Drain queue every 2s
        
        # Register callbacks
        self.mqtt_client.onOnlineCallback = self._on_online
        self.mqtt_client.onOfflineCallback = self._on_offline
        
        self.is_connected = False
    
    def _on_online(self):
        """Callback when client comes online"""
        print("[MQTT] Connected to AWS IoT Core")
        self.is_connected = True
    
    def _on_offline(self):
        """Callback when client goes offline"""
        print("[MQTT] Disconnected from AWS IoT Core")
        self.is_connected = False
    
    def connect(self) -> bool:
        """
        Connect to AWS IoT Core

        Returns:
            True if connection successful, False otherwise
        """
        try:
            print(f"[MQTT] Connecting to {self.endpoint}...")
            self.mqtt_client.connect()

            # Give callbacks time to fire and connection to stabilize
            for i in range(20):  # Try for up to 10 seconds
                time.sleep(0.5)
                if self.is_connected:
                    print("[MQTT] Connection confirmed via callback!")
                    return True

            # Callback didn't fire - verify connection by attempting a test publish
            print("[MQTT] Callback didn't fire, verifying connection with test publish...")
            try:
                # Try to publish a test message to verify connection
                test_topic = f"$aws/things/{self.client_id}/shadow/get"
                self.mqtt_client.publish(test_topic, "{}", 0)
                print("[MQTT] Test publish succeeded - connection is active")
                self.is_connected = True
                return True
            except Exception as pub_error:
                print(f"[MQTT] Test publish failed - connection not established: {pub_error}")
                return False

        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def subscribe(self, topic: str, callback) -> bool:
        """
        Subscribe to MQTT topic
        
        Args:
            topic: Topic to subscribe to (e.g., "command/gateway-001/+")
            callback: Function to call when message arrives
                     signature: callback(client, userdata, message)
        
        Returns:
            True if successful
        """
        try:
            self.mqtt_client.subscribe(topic, 1, callback)
            print(f"[MQTT] Subscribed to: {topic}")
            return True
        except Exception as e:
            print(f"[ERROR] Subscribe failed: {e}")
            return False
    
    def publish(self, topic: str, payload: dict, qos: int = 1) -> bool:
        """
        Publish message to MQTT topic
        
        Args:
            topic: Topic path (e.g., "vehicles/gateway-001/engine/rpm")
            payload: Dict to serialize to JSON
            qos: Quality of Service (0, 1)
        
        Returns:
            True if successful
        """
        try:
            message = json.dumps(payload)
            self.mqtt_client.publish(topic, message, qos)
            return True
        except Exception as e:
            print(f"[ERROR] Publish failed on {topic}: {e}")
            return False
    
    def disconnect(self):
        """Gracefully disconnect from AWS IoT Core"""
        try:
            self.mqtt_client.disconnect()
            print("[MQTT] Disconnected")
        except Exception as e:
            print(f"[ERROR] Disconnect failed: {e}")


def message_callback(client, userdata, message):
    """Handle incoming MQTT messages"""
    try:
        payload = json.loads(message.payload.decode('utf-8'))
        print(f"[RX] Topic: {message.topic}")
        print(f"    Payload: {json.dumps(payload, indent=2)}")
    except json.JSONDecodeError:
        print(f"[RX] Topic: {message.topic}")
        print(f"    Payload (raw): {message.payload.decode('utf-8')}")


if __name__ == '__main__':
    # # Create config
    # config = {
    #     'endpoint': 'a2tubkd8f0ljd4-ats.iot.eu-north-1.amazonaws.com',
    #     'thing_name': 'can-gateway',
    #     'client_id': 'can-gateway',  # Must match AWS IoT policy
    #     'cert_path': './certs/certificate.pem.crt',
    #     'key_path': './certs/private.pem.key',
    #     'ca_path': './certs/AmazonRootCA1.pem'
    # }
    
    # Read config from file
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Create client and connect
    client = CANGatewayMQTTClient('config.json')
    
    if not client.connect():
        print("[ERROR] Failed to connect")
        exit(1)
    
    # Subscribe to command topic (must match policy)
    client.subscribe('vehicle/can-gateway/commands', message_callback)
    
    # Publish test telemetry
    print("\n[TEST] Publishing sample telemetry...")
    for i in range(5):
        payload = {
            'timestamp': time.time(),
            'engine_rpm': 1500 + (i * 100),
            'vehicle_speed': 60 + i,
            'gateway_id': 'can-gateway',
            'sequence': i
        }
        client.publish('vehicle/can-gateway/telemetry', payload, qos=1)
        print(f"  Published: {payload}")
        time.sleep(1)
    
    # Keep client running to receive messages
    print("\n[INFO] Listening for commands... (Press Ctrl+C to exit)")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down...")
        client.disconnect()
        print("[INFO] Done")