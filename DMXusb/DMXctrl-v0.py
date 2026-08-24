#
#   DMXctrl-v0.py - DMX-Controller USB->RS485
#
#   20260711 - Gemini 3.5 Flash
#   20260711 - update Jens & Claude OPUS 4.8 R
#
#   FT232 USB zu RS485 Adapter + einfacher LED-Strahler
#   RS485 A -> DMX Pin 3 / Data+
#   RS485 B -> DMX Pin 2 / Data-
#

import time
import serial

# --- Konfiguration ---
PORT = 'COM8'           # Linux: '/dev/ttyUSB0'

DMX_CHANNELS = 64       # ausreichend Kanäle
#DMX_CHANNELS = 512      # max. Kanäle
FRAME_INTERVAL = 0.1    # Pause zwischen Frames, hier sehr lang
#FRAME_INTERVAL = 0.025  # ~40 fps (DMX-Maximum ~44 fps)


# öffne serielle Schnittstelle

ser = serial.Serial(
    port=PORT,
    baudrate=250000,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_TWO,
    timeout=1,
)


# Frame: 1 Start-Code + 512 Kanäle
dmx_data = bytearray(DMX_CHANNELS + 1)
dmx_data[0] = 0x00   # Start Code (0x00 = normale DMX-Daten)
dmx_data[1] = 255    # Kanal 1 (z.B. Gesamt)
dmx_data[2] = 0      # Kanal 2 (z.B. Rot)
dmx_data[3] = 255    # Kanal 3 (z.B. Grün)
dmx_data[4] = 255    # Kanal 4 (z.B. Blau)


def send_dmx_frame(data):
    # 1. BREAK (Leitung LOW), min. 88 µs
    ser.break_condition = True
    time.sleep(0.0001)

    # 2. MAB (Leitung HIGH), min. 8 µs
    ser.break_condition = False
    time.sleep(0.00002)

    # 3. Start-Code + Kanäle senden
    ser.write(data)
    ser.flush()


def main():
    print("Sende DMX-Frames... (Strg+C zum Beenden)")
    try:
        while True:
            send_dmx_frame(dmx_data)
            time.sleep(FRAME_INTERVAL)
    except KeyboardInterrupt:
        print("\ngestoppt.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
