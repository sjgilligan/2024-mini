"""
Response time - single-threaded with Firebase integration
"""

from machine import Pin
import time
import random
import json
import network
import socket
import urequests

N: int = 10  # Changed to 10 flashes
sample_ms = 10.0
on_ms = 500

ssid = "BU Guest (unencrypted)"
firebase_url = "https://mini-project-55318-default-rtdb.firebaseio.com/"

def connect():
    #Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid)
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        time.sleep(1)
    print(wlan.ifconfig())

def random_time_interval(tmin: float, tmax: float) -> float:
    return random.uniform(tmin, tmax)

def blinker(N: int, led: Pin) -> None:
    for _ in range(N):
        led.high()
        time.sleep(0.1)
        led.low()
        time.sleep(0.1)

def write_json(json_filename: str, data: dict) -> None:
    with open(json_filename, "w") as f:
        json.dump(data, f)

def send_to_firebase(data: dict) -> None:
    try:
        response = urequests.post(firebase_url + "scores.json", json=data)
        print("Data sent to Firebase. Response:", response.text)
        response.close()
    except Exception as e:
        print("Error sending data to Firebase:", str(e))

def scorer(t: list[int | None]) -> None:
    misses = t.count(None)
    print(f"You missed the light {misses} / {len(t)} times")

    t_good = [x for x in t if x is not None]

    print(t_good)

    if t_good:
        avg_response = sum(t_good) / len(t_good)
        min_response = min(t_good)
        max_response = max(t_good)
    else:
        avg_response = min_response = max_response = None

    score = (len(t) - misses) / len(t)

    data = {
        "average response time": avg_response,
        "minimum response time": min_response,
        "maximum response time": max_response,
        "score": score
    }

    now: tuple[int] = time.localtime()
    now_str = "-".join(map(str, now[:3])) + "T" + "_".join(map(str, now[3:6]))
    filename = f"score-{now_str}.json"

    print("write", filename)
    write_json(filename, data)
    send_to_firebase(data)

if __name__ == "__main__":
    connect()
    led = Pin("LED", Pin.OUT)
    button = Pin(28, Pin.IN, Pin.PULL_UP)

    t: list[int | None] = []

    blinker(3, led)

    for i in range(N):
        time.sleep(random_time_interval(0.5, 5.0))

        led.high()

        tic = time.ticks_ms()
        t0 = None
        while time.ticks_diff(time.ticks_ms(), tic) < on_ms:
            if button.value() == 0:
                t0 = time.ticks_diff(time.ticks_ms(), tic)
                led.low()
                break
        t.append(t0)

        led.low()

    blinker(5, led)

    scorer(t)
