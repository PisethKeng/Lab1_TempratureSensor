# esp32_dht22_relay_threshold_bot.py

import time
import network
import urequests as requests
import machine
import dht

from env_loader import load_env

env = load_env()

# ==== USER SETTINGS ====
WIFI_SSID = env.get("WIFI_SSIDS", "")
WIFI_PSK  = env.get("WIFI_PSKS", "")

BOT_TOKEN = env.get("BOT_TOKENS", "")
CHAT_ID   = env.get("CHAT_ID", "")
DHT_PIN = 4                  # GPIO for DHT11 data
RELAY_PIN = 2                # GPIO for relay
CHECK_INTERVAL = 5         # seconds between checks
TEMP_THRESHOLD = 24.0        # °C
# =======================

# --- Relay setup ---
relay = machine.Pin(RELAY_PIN, machine.Pin.OUT)
relay.value(0)  # OFF at start
relay_forced_on = False      # Track if ON was commanded

def relay_on():
    global relay_forced_on
    relay.value(1)
    relay_forced_on = True

def relay_off():
    global relay_forced_on
    relay.value(0)
    relay_forced_on = False

def relay_is_on():
    return relay.value() == 1

# --- Wi-Fi ---
def wifi_connect(ssid, psk, timeout=20):
    sta = network.WLAN(network.STA_IF)
    if not sta.active():
        sta.active(True)
    if not sta.isconnected():
        print("Connecting to Wi-Fi:", ssid)
        sta.connect(ssid, psk)
        t0 = time.ticks_ms()
        while not sta.isconnected():
            if time.ticks_diff(time.ticks_ms(), t0) > timeout*1000:
                raise OSError("Wi-Fi timed out")
            time.sleep(0.3)
    print("Wi-Fi OK:", sta.ifconfig())

# --- Telegram helpers ---
TG_BASE = "https://api.telegram.org/bot{}".format(BOT_TOKEN)

def send_message(chat_id, text):
    try:
        url = TG_BASE + "/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        r = requests.post(url, json=payload)
        r.close()
    except Exception as e:
        print("send_message error:", e)

def get_updates(offset=None, timeout=5):
    try:
        url = TG_BASE + "/getUpdates?timeout={}".format(timeout)
        if offset:
            url += "&offset={}".format(offset)
        r = requests.get(url)   # MicroPython urequests: no params kw
        data = r.json()
        r.close()
        return data
    except Exception as e:
        print("get_updates error:", e)
        return {}

# --- Handle commands ---
def handle_cmd(chat_id, text, current_temp):
    t = (text or "").strip().lower()
    if t in ("/on", "on"):
        if current_temp > TEMP_THRESHOLD:
            relay_on()
            send_message(chat_id, "Relay: ON (Temp {:.1f}°C)".format(current_temp))
        else:
            send_message(chat_id, "Temp {:.1f}°C is not above {:.1f}°C → Relay stays OFF".format(current_temp, TEMP_THRESHOLD))
    elif t in ("/off", "off"):
        relay_off()
        send_message(chat_id, "Relay: OFF")
    elif t in ("/status", "status"):
        send_message(chat_id, "Relay is {} (Temp {:.1f}°C)".format("ON" if relay_is_on() else "OFF", current_temp))
    elif t in ("/whoami", "whoami"):
        send_message(chat_id, "Your chat id is: {}".format(chat_id))
    elif t in ("/help", "/start", "help"):
        send_message(chat_id, "Commands:\n/on\n/off\n/status\n/whoami")
    else:
        send_message(chat_id, "Unknown. Try /on, /off, /status, /whoami")

# --- DHT11 ---
sensor = dht.DHT11(machine.Pin(DHT_PIN))
def read_dht11():
    for _ in range(3):
        try:
            sensor.measure()
            return sensor.temperature(), sensor.humidity()
        except Exception:
            time.sleep(2)
    raise OSError("DHT11 failed")

# --- Main loop ---
def main():
    wifi_connect(WIFI_SSID, WIFI_PSK)

    last_temp = None
    update_offset = None

    while True:
        try:
            temp, hum = read_dht11()
            print("Temp:", temp, "Hum:", hum)

            # 1) Alert when crossing ABOVE threshold
            if temp > TEMP_THRESHOLD and (last_temp is None or last_temp <= TEMP_THRESHOLD):
                send_message(CHAT_ID, "⚠️ Temp above {:.1f}°C! Now {:.1f}°C".format(TEMP_THRESHOLD, temp))

            # 2) Auto-OFF + alerts when crossing BELOW/AT threshold
            if last_temp is not None and last_temp > TEMP_THRESHOLD and temp <= TEMP_THRESHOLD:
                if relay_forced_on:
                    relay_off()
                    # Console & Telegram alerts when auto-off happens
                    print("Auto-OFF: temp dropped to {:.1f}°C (<= {:.1f}°C). Relay OFF.".format(temp, TEMP_THRESHOLD))
                    send_message(CHAT_ID, "✅ Temp {:.1f}°C ≤ {:.1f}°C — Relay turned OFF automatically".format(temp, TEMP_THRESHOLD))
                else:
                    # Optional informational message when relay already OFF
                    print("Temp back to normal (relay already OFF). Now {:.1f}°C.".format(temp))
                    send_message(CHAT_ID, "ℹ️ Temp back to normal (≤ {:.1f}°C). Relay already OFF.".format(TEMP_THRESHOLD))

            last_temp = temp

            # 3) Poll Telegram for commands
            updates = get_updates(offset=update_offset)
            if "result" in updates:
                for upd in updates["result"]:
                    update_offset = upd["update_id"] + 1
                    if "message" in upd and "text" in upd["message"]:
                        cid = upd["message"]["chat"]["id"]
                        text = upd["message"]["text"]
                        handle_cmd(cid, text, temp)

        except Exception as e:
            print("Loop error:", e)

        time.sleep(CHECK_INTERVAL)

# ---- Run ----
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        relay_off()
        print("Stopped.")
