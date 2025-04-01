import os
import RPi.GPIO as GPIO
from lib_nrf24 import NRF24
import spidev
import time
import picamera

# Define pipe address (must match Arduino transmitter)
pipes = [b"00001"]

# Initialize nRF24L01+
radio = NRF24(GPIO, spidev.SpiDev())
radio.begin(0, 17)  # SPI bus 0, CE on GPIO17
radio.setPayloadSize(32)
radio.setChannel(0x76)
radio.setDataRate(NRF24.BR_250KBPS)
radio.setPALevel(NRF24.PA_HIGH)
radio.openReadingPipe(1, pipes[0])
radio.startListening()

# Initialize camera
camera = picamera.PiCamera()

# Get free storage percentage
def get_storage_status():
    statvfs = os.statvfs("/")
    total = (statvfs.f_blocks * statvfs.f_frsize) / (1024 ** 3)
    free = (statvfs.f_bfree * statvfs.f_frsize) / (1024 ** 3)
    return (free / total) * 100

# Get battery percentage (if available)
def get_battery_status():
    try:
        with open("/sys/class/power_supply/BAT0/capacity", "r") as f:
            return int(f.read().strip())
    except:
        return -1  # No battery data found

# Main loop: receive command or send status every few seconds
last_status_time = 0
status_interval = 10  # seconds

print("[Receiver Ready] Listening for CAPTURE and sending status...")

while True:
    now = time.time()

    # -- Receive Mode --
    radio.startListening()
    if radio.available():
        receivedMessage = []
        radio.read(receivedMessage, radio.getDynamicPayloadSize())
        message = "".join([chr(n) for n in receivedMessage if 32 <= n <= 126])

        print(f"[Command Received] {message}")

        if message == "CAPTURE":
            print("Trigger received. Capturing image...")
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = f"/home/pi/image_{timestamp}.jpg"
            camera.capture(filepath)
            print(f"[Image Saved] {filepath}")

    # -- Send status every N seconds --
    if now - last_status_time >= status_interval:
        storage = get_storage_status()
        battery = get_battery_status()
        status_msg = f"{int(storage)}%|{int(battery)}%".encode('utf-8')

        radio.stopListening()  # Switch to TX mode
        result = radio.write(list(status_msg))  # Send encoded message
        radio.startListening()  # Back to RX mode

        print(f"[Status Sent] Storage: {storage:.2f}%, Battery: {battery}%, Success: {result}")
        last_status_time = now

    time.sleep(0.05)  # Light delay to prevent busy looping
