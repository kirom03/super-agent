import json
import time
from typing import Dict, Any, List
import serial.tools.list_ports
import paho.mqtt.client as mqtt
from core.config import MQTT_BROKER, MQTT_PORT, DEFAULT_SERIAL_BAUDRATE

def serial_scan_ports() -> str:
    """Scans all active USB COM serial ports on the laptop for microcontrollers (ESP32, Arduino, STM32, Pico)."""
    try:
        ports = serial.tools.list_ports.comports()
        detected = []
        for port in ports:
            detected.append({
                "port": port.device,
                "description": port.description,
                "hardware_id": port.hwid,
                "manufacturer": getattr(port, "manufacturer", "Unknown") or "Unknown",
                "vid": hex(port.vid) if port.vid else None,
                "pid": hex(port.pid) if port.pid else None
            })
        return json.dumps({
            "status": "success",
            "count": len(detected),
            "ports": detected
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

def mqtt_publish(topic: str, payload: str, broker: str = MQTT_BROKER, port: int = MQTT_PORT) -> str:
    """Publishes an MQTT message to a broker for smart home / IoT actuator control."""
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.connect(broker, port, keepalive=10)
        res = client.publish(topic, payload, qos=1)
        res.wait_for_publish(timeout=5.0)
        client.disconnect()
        return json.dumps({
            "status": "success",
            "broker": broker,
            "port": port,
            "topic": topic,
            "payload": payload,
            "message": "MQTT message delivered."
        })
    except Exception as e:
        return json.dumps({"status": "error", "topic": topic, "error": str(e)})

def mqtt_read_telemetry(topic: str, timeout_sec: int = 5, broker: str = MQTT_BROKER, port: int = MQTT_PORT) -> str:
    """Subscribes and listens to an MQTT telemetry topic for sensor data."""
    received_messages = []

    def on_message(client, userdata, msg):
        try:
            received_messages.append({
                "topic": msg.topic,
                "payload": msg.payload.decode("utf-8", errors="replace"),
                "timestamp": time.time()
            })
        except Exception:
            pass

    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.on_message = on_message
        client.connect(broker, port, keepalive=15)
        client.subscribe(topic)
        client.loop_start()

        start = time.time()
        while time.time() - start < timeout_sec:
            if received_messages:
                break
            time.sleep(0.2)

        client.loop_stop()
        client.disconnect()

        return json.dumps({
            "status": "success",
            "topic": topic,
            "count": len(received_messages),
            "messages": received_messages
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "topic": topic, "error": str(e)})
