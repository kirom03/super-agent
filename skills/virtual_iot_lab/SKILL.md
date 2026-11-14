# Virtual IoT Lab Skill

Allows testing physical computing without physical hardware:
1. Controls the built-in virtual ESP32 simulator via MQTT.
2. Topics:
   - `super_agent/laptop/relay` (commands: `ON`, `OFF`)
   - `super_agent/laptop/sensors` (telemetry: `temperature`, `humidity`, `uptime`)
3. Generates Arduino C++ and MicroPython code ready to flash onto physical ESP32/Arduino boards.
