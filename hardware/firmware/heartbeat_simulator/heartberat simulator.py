import RPi.GPIO as GPIO
import time

HEATBEAT_PIN=17
HEARTBEAT_INTERVAL_S= 1.0

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(HEART_PIN,GPIO.OUT)
    print(f"Heartbeat simulator initialized on GPIO{HEATBEAT_PIN}.")

def main():
    print("Starting heartbeat signal...")
    print("Press Ctrl+C to simulate an OBC freeze.")

    try:
        is_high=True
        while True:
            if is_high:
                GPIO.output(HEARTBEAT_PIN,GPIO.HIGH)
                print("Heartbeat: HIGH")
            else:
                GPIO.output(HEARTBEAT_PIN,GPIO.LOW)
                print("Heartbeat: LOW")
            
            is_high= not is_high
            time.sleep(HEARTBEAT_INTERVAL_S)
    
    except KeyboardInterrupt:
        print("\nSimulation stopped by user (Simulating OBC freeze).")
        print("Heartbeat will now cease. Guardian should intervene.")
    
    finally:
        GPIO.cleanup()
        print("GPIO cleanup complete. Exiting.")

if __name__ == "__main__":
    setup()
    main()
        