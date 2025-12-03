"""
Flask application with scheduled MQTT publishing to AWS IoT Core
- Publishes telemetry at configurable intervals
- Provides REST API for health checks and manual publishing
- Runs as a containerized service
"""

import json
import time
import threading
from pathlib import Path
from flask import Flask, jsonify, request
from basic_mqtt_client import CANGatewayMQTTClient

app = Flask(__name__)

# Global client instance
mqtt_client = None
config = None
publisher_thread = None
stop_event = threading.Event()

def load_config():
    """Load configuration from config.json"""
    global config
    with open('config.json', 'r') as f:
        config = json.load(f)
    # Set default publish interval if not specified (5 minutes)
    if 'publish_interval_seconds' not in config:
        config['publish_interval_seconds'] = 300
    return config

def initialize_mqtt():
    """Initialize and connect MQTT client"""
    global mqtt_client
    try:
        mqtt_client = CANGatewayMQTTClient('config.json')
        if mqtt_client.connect():
            app.logger.info("MQTT client connected successfully")
            return True
        else:
            app.logger.error("Failed to connect MQTT client")
            return False
    except Exception as e:
        app.logger.error(f"Error initializing MQTT client: {e}")
        return False

def publish_telemetry():
    """Publish telemetry data to AWS IoT Core"""
    if mqtt_client and mqtt_client.is_connected:
        payload = {
            'timestamp': time.time(),
            'gateway_id': config.get('thing_name', 'can-gateway'),
            'status': 'online',
            'message': 'Scheduled telemetry data'
        }

        topic = f"vehicle/{config.get('thing_name', 'can-gateway')}/telemetry"
        success = mqtt_client.publish(topic, payload, qos=1)

        if success:
            app.logger.info(f"Published to {topic}: {payload}")
            return True
        else:
            app.logger.error(f"Failed to publish to {topic}")
            return False
    else:
        app.logger.warning("MQTT client not connected, skipping publish")
        return False

def publisher_loop():
    """Background thread that publishes telemetry at configured intervals"""
    app.logger.info(f"Publisher thread started with interval: {config['publish_interval_seconds']}s")

    while not stop_event.is_set():
        try:
            publish_telemetry()
        except Exception as e:
            app.logger.error(f"Error in publisher loop: {e}")

        # Wait for the configured interval or until stop event
        stop_event.wait(timeout=config['publish_interval_seconds'])

    app.logger.info("Publisher thread stopped")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'mqtt_connected': mqtt_client.is_connected if mqtt_client else False,
        'config': {
            'endpoint': config.get('endpoint', 'N/A'),
            'thing_name': config.get('thing_name', 'N/A'),
            'publish_interval_seconds': config.get('publish_interval_seconds', 300)
        }
    }), 200

@app.route('/publish', methods=['POST'])
def manual_publish():
    """Manually trigger a publish"""
    try:
        # Allow custom payload from request
        if request.json:
            payload = request.json
            payload['timestamp'] = time.time()
        else:
            payload = {
                'timestamp': time.time(),
                'gateway_id': config.get('thing_name', 'can-gateway'),
                'status': 'online',
                'message': 'Manual publish'
            }

        topic = f"vehicle/{config.get('thing_name', 'can-gateway')}/telemetry"
        success = mqtt_client.publish(topic, payload, qos=1)

        if success:
            return jsonify({
                'status': 'success',
                'topic': topic,
                'payload': payload
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to publish'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify({
        'endpoint': config.get('endpoint', 'N/A'),
        'thing_name': config.get('thing_name', 'N/A'),
        'client_id': config.get('client_id', 'N/A'),
        'publish_interval_seconds': config.get('publish_interval_seconds', 300)
    }), 200

def start_publisher_thread():
    """Start the background publisher thread"""
    global publisher_thread
    publisher_thread = threading.Thread(target=publisher_loop, daemon=True)
    publisher_thread.start()

def shutdown():
    """Gracefully shutdown the application"""
    app.logger.info("Shutting down...")
    stop_event.set()
    if publisher_thread:
        publisher_thread.join(timeout=5)
    if mqtt_client:
        mqtt_client.disconnect()
    app.logger.info("Shutdown complete")

if __name__ == '__main__':
    # Load configuration
    load_config()

    # Initialize MQTT client
    if not initialize_mqtt():
        app.logger.error("Failed to initialize MQTT client, exiting...")
        exit(1)

    # Start publisher thread
    start_publisher_thread()

    # Run Flask app
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        shutdown()
