import serial
import struct
import time

# Configuration
SERIAL_PORT = "/dev/ttyAMA0"
BAUD_RATE = 115200

def create_msp_packet(cmd, payload):
    size = len(payload)
    checksum = size ^ cmd
    for b in payload:
        checksum ^= b
    
    header = b'\x24\x4D\x3C' # $M<
    return header + struct.pack('<BB', size, cmd) + payload + struct.pack('<B', checksum)

def send_rc_channels(ser, roll, pitch, throttle, yaw, aux1):
    # Betaflight expects 8 channels minimum for MSP_SET_RAW_RC
    # Order: Roll, Pitch, Throttle, Yaw, Aux1, Aux2, Aux3, Aux4
    channels = [roll, pitch, throttle, yaw, aux1, 1000, 1000, 1000]
    payload = struct.pack('<8H', *channels)
    packet = create_msp_packet(200, payload)
    ser.write(packet)

def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        print("Starting motor test... Press Ctrl+C to STOP and DISARM")

        # 1. Start sending 'Idle' data (Disarmed, Low Throttle)
        # We need a stream of data BEFORE arming so the FC sees a valid link
        for _ in range(50):
            send_rc_channels(ser, 1500, 1500, 1000, 1500, 1000)
            time.sleep(0.02) # 50Hz

        # 2. ARM the drone (Aux 1 -> 2000)
        print("ARMING...")
        for _ in range(50):
            send_rc_channels(ser, 1500, 1500, 1000, 1500, 2000)
            time.sleep(0.02)

        # 3. Spin Motors (Throttle -> 1150)
        print("SPINNING - LOW SPEED")
        while True:
            # 1150 is usually just above the minimum spin threshold
            send_rc_channels(ser, 1500, 1500, 1500, 1500, 2000)
            time.sleep(0.02)

    except KeyboardInterrupt:
        print("\nSTOPPING - DISARMING")
        # Send Disarm and Zero Throttle before closing
        for _ in range(10):
            send_rc_channels(ser, 1500, 1500, 1000, 1500, 1000)
            time.sleep(0.02)
        ser.close()

if __name__ == "__main__":
    main()
