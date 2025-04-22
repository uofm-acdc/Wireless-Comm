import serial
import time
import picamera

# Adjust the port name if needed
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 57600

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
camera = picamera.PiCamera()

print("Listening for CAPTURE command...")

while True:
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').strip()
        print(f"Received: {line}")

        if line == "CAPTURE":
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"/home/pi/image_{timestamp}.jpg"
            print(f"Capturing image: {filename}")
            camera.capture(filename)
            print("Image saved.")
