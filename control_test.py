def send_rc(roll, pitch, throttle, yaw):
    # Prepare 8 channels (1000-2000)
    channels = [roll, pitch, throttle, yaw, 1000, 1000, 1000, 1000]
    payload = struct.pack('<8H', *channels) # 8 unsigned shorts
    
    size = len(payload)
    type_code = 200
    
    # Create the MSP packet
    header = b'\x24\x4D\x3C'
    checksum = size ^ type_code
    for b in payload:
        checksum ^= b
        
    full_packet = header + struct.pack('<BB', size, type_code) + payload + struct.pack('<B', checksum)
    ser.write(full_packet)
