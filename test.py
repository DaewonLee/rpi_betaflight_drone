import serial
import time

# For RPi 5 pins 8/10, the device is usually /dev/ttyAMA0
SERIAL_PORT = "/dev/ttyAMA0"
BAUD_RATE = 115200

def test_connection():
    try:
        # Initialize Serial
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        
        # MSP_API_VERSION Request Packet
        # $M< [size:0] [code:1] [checksum:1]
        # Checksum is XOR of size(0) and code(1) = 1
        request = b'\x24\x4D\x3C\x00\x01\x01'
        
        print(f"Attempting to talk to Flight Controller on {SERIAL_PORT}...")
        ser.write(request)
        
        # Expecting 9 bytes back: $M> [size:3] [code:1] [protocol] [major] [minor] [crc]
        response = ser.read(9)
        
        if response and response.startswith(b'$M>'):
            print("--- SUCCESS! ---")
            print(f"Raw Hex: {response.hex()}")
            # The API version is in bytes 6 and 7
            v_major = response[6]
            v_minor = response[7]
            print(f"Betaflight API Version: {v_major}.{v_minor}")
        else:
            print("--- FAILURE ---")
            print("No valid response. Possible issues:")
            print("- Check if MSP is enabled on UART1 in Betaflight.")
            print("- Check if TX/RX wires are swapped.")
            print("- Ensure the FC is powered (sometimes requires battery).")
            
        ser.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_connection()
