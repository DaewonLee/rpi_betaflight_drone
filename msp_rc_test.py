import argparse
import struct
import sys
import time

import serial


MSP_SET_RAW_RC = 200


def build_msp_v1(command, payload=b""):
    size = len(payload)
    checksum = size ^ command
    for byte in payload:
        checksum ^= byte
    return b"$M<" + bytes([size, command]) + payload + bytes([checksum])


def send_rc(ser, channels):
    payload = struct.pack("<8H", *channels)
    ser.write(build_msp_v1(MSP_SET_RAW_RC, payload))


def build_channels(channel_map, roll, pitch, throttle, yaw, aux1):
    channel_map = channel_map.upper()
    if len(channel_map) < 4 or any(name not in "AETR" for name in channel_map[:4]):
        raise ValueError("channel map must start with A, E, T, and R, for example TAER1234")

    values = {
        "A": roll,
        "E": pitch,
        "T": throttle,
        "R": yaw,
    }

    channels = [values[name] for name in channel_map[:4]]
    channels.extend([aux1, 1000, 1000, 1000])
    return channels


def main():
    parser = argparse.ArgumentParser(
        description="Send MSP receiver channels to Betaflight. Remove props first."
    )
    parser.add_argument("--port", default="/dev/ttyAMA0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--arm", action="store_true")
    parser.add_argument("--throttle", type=int, default=1000)
    parser.add_argument("--roll", type=int, default=1500)
    parser.add_argument("--pitch", type=int, default=1500)
    parser.add_argument("--yaw", type=int, default=1500)
    parser.add_argument("--channel-map", default="TAER1234")
    parser.add_argument("--prearm-seconds", type=float, default=2.0)
    parser.add_argument("--seconds", type=float, default=10.0)
    parser.add_argument("--rate", type=float, default=50.0)
    args = parser.parse_args()

    throttle = max(1000, min(2000, args.throttle))
    aux1 = 1800 if args.arm else 1000
    channels = build_channels(
        args.channel_map.upper(),
        args.roll,
        args.pitch,
        throttle,
        args.yaw,
        aux1,
    )

    safe_channels = build_channels(
        args.channel_map.upper(), 1500, 1500, 1000, 1500, 1000
    )
    period = 1.0 / args.rate
    end_time = time.monotonic() + args.seconds

    with serial.Serial(args.port, args.baud, timeout=0.1) as ser:
        if args.arm and args.prearm_seconds > 0:
            print(
                f"Sending disarmed values for {args.prearm_seconds:.1f}s...",
                flush=True,
            )
            prearm_end_time = time.monotonic() + args.prearm_seconds
            while time.monotonic() < prearm_end_time:
                send_rc(ser, safe_channels)
                time.sleep(period)

        print(
            "Sending RC: "
            f"roll={args.roll} pitch={args.pitch} yaw={args.yaw} "
            f"throttle={throttle} aux1={aux1} "
            f"channel_map={args.channel_map.upper()} "
            f"for {args.seconds:.1f}s",
            flush=True,
        )
        while time.monotonic() < end_time:
            send_rc(ser, channels)
            time.sleep(period)

        print("Sending safe/disarm values...", flush=True)
        for _ in range(25):
            send_rc(ser, safe_channels)
            time.sleep(period)
        print("Done.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
