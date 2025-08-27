## ESP32 DHT11 Relay Threshold Bot

Control Relay from telegram chat while monitoring temperature from DHT11 sensor on a ESP32.

## Project Criteria 

1. Read temperature → send to Telegram.

2. Send only when it is above 30 °C.

3. Enable remote control: Users can send /on and /off from Telegram.

4. Threshold logic: When the temperature is above 30 °C and /on is sent, the relay activates. When the temperature drops below 30 °C, the relay automatically switches OFF.

5. Group bot support: Works inside Telegram group chats instead of just direct bot chats.

## Features 

_ Real‑time temperature and humidity monitoring with DHT11/DHT22.

_ Telegram bot interface for remote relay control.

_ Auto‑alerts when temperature crosses the configured threshold.

_ Automatic relay OFF when temperature normalizes.

_ Supports group chats with Telegram bots.

## Tech Stack

+ Hardware: ESP32, DHT11/DHT22 sensor, Relay module

+ Software: MicroPython, Telegram Bot API, urequests

## Learning Outcome 

_Applied IoT development using ESP32 with sensors and actuators.

_Implemented Telegram bot integration for hardware control.

_Practiced event‑driven programming with real‑world thresholds.

_Explored automation and remote monitoring for smart systems.


