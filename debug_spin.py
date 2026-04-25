import serial
import struct
import time

SERIAL_PORT = "/dev/ttyAMA0"
BAUD_RATE = 115200

def create_msp_packet(cmd, payload):
    size = len(payload)
    checksum = size ^ cmd
    for b in payload: checksum ^= b
    return b'\x24\x4D\x3C' + struct.pack('<BB', size, cmd) + payload + struct.pack('<B', checksum)

def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.01) # Low timeout
        print("Sending Heartbeat... Watch for Flag 0b10 to disappear.")
        
        while True:
            # 1. SEND RC COMMANDS (The Heartbeat)
            # Roll=1500, Pitch=1500, Throttle=1000 (Low), Yaw=1500, Aux1=1000 (Disarmed)
            # Note: We start DISARMED to clear the RX_LOSS first.
            channels = [1500, 1500, 1000, 1500, 1000, 1000, 1000, 1000]
            payload = struct.pack('<8H', *channels)
            ser.write(create_msp_packet(200, payload))

            # 2. QUICKLY CHECK STATUS
            ser.write(create_msp_packet(101, b''))
            response = ser.read(30) # Read a chunk
            
            if response and len(response) > 15:
                # Find the start of the MSP_STATUS response in the buffer
                try:
                    idx = response.index(b'\x65') # 101 is 0x65
                    status_payload = response[idx+1:idx+11]
                    flags = struct.unpack('<I', status_payload[6:10])[0]
                    
                    if flags & (1 << 2):
                        print("\rStatus: STILL BLOCKED BY RX_LOSS (Bit 2)", end="")
                    elif flags == 0:
                        print("\rStatus: READY! Press Ctrl+C to stop.", end="")
                    else:
                        print(f"\rStatus: Flags Active: {bin(flags)}", end="")
                except:
                    pass

            time.sleep(0.02) # Constant 50Hz

    except KeyboardInterrupt:
        ser.close()

if __name__ == "__main__":
    main()
