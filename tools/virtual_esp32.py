import time
import random
import threading
import paho.mqtt.client as mqtt
from core.config import MQTT_BROKER, MQTT_PORT

class VirtualESP32:
    def __init__(self, broker=MQTT_BROKER, port=MQTT_PORT):
        self.broker = broker
        self.port = port
        self.base_topic = "super_agent/laptop"
        self.relay_topic = f"{self.base_topic}/relay"
        self.sensor_topic = f"{self.base_topic}/sensors"
        
        self.relay_state = "OFF"
        self.led_state = "OFF"
        self.temperature = 28.0
        self.humidity = 60.0
        self.is_running = False
        self.client = None
        self._thread = None

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self.is_running = False
        if self.client:
            try:
                self.client.disconnect()
            except Exception:
                pass

    def _run(self):
        def on_message(client, userdata, msg):
            topic = msg.topic
            payload = msg.payload.decode("utf-8", errors="replace").strip().upper()
            if topic == self.relay_topic:
                if payload in ["ON", "1", "TRUE"]:
                    self.relay_state = "ON"
                else:
                    self.relay_state = "OFF"

        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            self.client.on_message = on_message
            self.client.connect(self.broker, self.port, keepalive=30)
            self.client.subscribe(self.relay_topic)
            self.client.loop_start()

            while self.is_running:
                # Fluctuate simulated temperature slightly
                self.temperature = round(27.0 + random.uniform(-0.8, 1.5), 1)
                self.humidity = round(58.0 + random.uniform(-2.0, 3.0), 1)

                telemetry = {
                    "device": "Virtual_ESP32_Node",
                    "relay": self.relay_state,
                    "temperature_c": self.temperature,
                    "humidity_percent": self.humidity,
                    "uptime_sec": int(time.time())
                }
                import json
                self.client.publish(self.sensor_topic, json.dumps(telemetry))
                time.sleep(4.0)

            self.client.loop_stop()
        except Exception:
            pass

    def get_state(self):
        return {
            "running": self.is_running,
            "relay": self.relay_state,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "broker": self.broker
        }

virtual_esp32 = VirtualESP32()
