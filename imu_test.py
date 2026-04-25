import serial
import struct

ser = serial.Serial("/dev/ttyAMA0", 115200, timeout=0.1)

def get_imu():
    # MSP_RAW_IMU request
    cmd = b'\x24\x4D\x3C\x00\x66\x66' 
    ser.write(cmd)
    
    # Header(3) + Size(1) + Type(1) + Data(18) + CRC(1) = 24 bytes
    data = ser.read(24)
    
    if len(data) == 24 and data[4] == 102:
        # Unpack 9 signed shorts (h)
        imu_values = struct.unpack('<9h', data[5:23])
        return {
            "acc": imu_values[0:3],
            "gyro": imu_values[3:6],
            "mag": imu_values[6:9]
        }
    return None

while True:
    imu = get_imu()
    if imu:
        print(f"Acc: {imu['acc']} | Gyro: {imu['gyro']}")
