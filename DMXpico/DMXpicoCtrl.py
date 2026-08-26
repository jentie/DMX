#
#   DMXpico-Ctrl.py - DMX-Fader-Oberflaeche fuer Raspberry Pi Pico
#
#   Sendet Hex-Datenpaare "KANAL,WERT\n" an den Pico (USB-CDC).
#   Der Pico erzeugt daraus die DMX-Frames (RS485, Kanal 0 / GP0).
#
#   PC -> Pico Protokoll:  <KanalHex>,<WertHex>\n   z.B. "02,FF"
#

import tkinter as tk
import serial
import serial.tools.list_ports
import threading
import time


# --- PICO-VERBINDUNG ---

def find_pico_port():
    """Erkennung des Raspberry Pi Pico (RP2040 USB-CDC, VID=0x2E8A).
    Gibt (device, info_text) zurueck oder (None, info_text)."""
    for port in serial.tools.list_ports.comports():
        # Methode 1: Hardware-ID (RP2040: VID=0x2E8A)
        if port.vid == 0x2E8A:
            return port.device, f"Pico ueber Hardware-ID: {port.device}"

        # Methode 2 (Fallback): Textpruefung
        if port.description and ("Pico" in port.description
                                 or "RP2040" in port.description
                                 or "Board CDC" in port.description):
            return port.device, f"Pico ueber Textbeschreibung: {port.device} ({port.description})"

    return None, "Kein Raspberry Pi Pico gefunden."


target_port, port_info = find_pico_port()

status_text = ""
status_ok = False

try:
    if target_port:
        ser = serial.Serial(
            port=target_port,
            baudrate=115200,     # USB-CDC: Wert egal, muss aber gesetzt sein
            timeout=1,
        )
        status_text = f"✓ Pico verbunden – {port_info}"
        status_ok = True
    else:
        ser = None
        status_text = f"⚠ Simulationsmodus – {port_info}"
        status_ok = False
except Exception as e:
    ser = None
    status_text = f"✗ Fehler beim Oeffnen des Ports: {e}"
    status_ok = False


# Letzte gesendete Werte je Kanal (zum Erkennen von Aenderungen)
# Kanaele 1..4; None = noch nie gesendet
last_sent = {1: None, 2: None, 3: None, 4: None}


def send_pair(channel, value):
    """Sendet ein Hex-Datenpaar KANAL,WERT an den Pico."""
    value = max(0, min(255, int(value)))
    if last_sent.get(channel) == value:
        return  # unveraendert -> nicht senden
    last_sent[channel] = value

    if ser:
        try:
            line = f"{channel:02X},{value:02X}\n"
            ser.write(line.encode("ascii"))
        except Exception as e:
            update_status(f"✗ Sende-Fehler: {e}", ok=False)


# --- GUI LOGIK ---

def update_status(text, ok):
    """Aktualisiert die Statuszeile thread-sicher."""
    def _apply():
        color = "#1a7f37" if ok else "#c1121f"
        lbl_status.config(text=text, fg=color)
    root.after(0, _apply)


def update_channels(*args):
    """Berechnet die DMX-Werte aus den Slidern und dem Master und sendet sie."""
    master_ratio = slider_master.get() / 255.0

    master_val = max(0, min(255, int(round(slider_master.get()))))
    r_val = max(0, min(255, int(round(slider_r.get() * master_ratio))))
    g_val = max(0, min(255, int(round(slider_g.get() * master_ratio))))
    b_val = max(0, min(255, int(round(slider_b.get() * master_ratio))))

    # An Pico senden (nur bei Aenderung)
    send_pair(1, master_val)   # Kanal 1: Gesamt
    send_pair(2, r_val)        # Kanal 2: Rot
    send_pair(3, g_val)        # Kanal 3: Gruen
    send_pair(4, b_val)        # Kanal 4: Blau

    lbl_master_val.config(text=f"{master_val}")
    lbl_r_val.config(text=f"{r_val} ({int(round(slider_r.get()))})")
    lbl_g_val.config(text=f"{g_val} ({int(round(slider_g.get()))})")
    lbl_b_val.config(text=f"{b_val} ({int(round(slider_b.get()))})")


# --- ANWENDUNGS-START ---

root = tk.Tk()
root.title("Pico DMX RGB Controller")
root.geometry("420x440")

# --- GUI LAYOUT ---
color_bg = "#f9f9f9"
color_slider_trough = "#d0d0d0"
color_master = "#808080"
color_red = "#A52A2A"
color_green = "#004B23"
color_blue = "#000080"

root.configure(bg=color_bg)

slider_opts = {
    'from_': 255,
    'to': 0,
    'orient': tk.VERTICAL,
    'command': update_channels,
    'resolution': 1,
    'showvalue': False,
    'width': 25,
    'length': 250,
    'sliderlength': 30,
    'bd': 0,
    'highlightthickness': 0
}

main_frame = tk.Frame(root, bg=color_bg)
main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(20, 5))

for i in range(4):
    main_frame.columnconfigure(i, weight=1)
main_frame.rowconfigure(0, weight=1)

# --- 1. Master Slider (Gesamt) ---
slider_master = tk.Scale(main_frame, **slider_opts,
                         troughcolor=color_slider_trough,
                         activebackground=color_master, bg=color_bg)
slider_master.set(255)
slider_master.grid(row=0, column=0, sticky="ns", padx=10)

tk.Label(main_frame, text="Gesamt\n(Ch 1)", bg=color_bg, fg="black",
         font=("Arial", 10, "bold")).grid(row=1, column=0, pady=(10, 5))
lbl_master_val = tk.Label(main_frame, text="255", bg=color_bg, fg="black",
                          font=("Arial", 10), width=10, anchor="center")
lbl_master_val.grid(row=2, column=0)

# --- 2. Rot Slider ---
slider_r = tk.Scale(main_frame, **slider_opts,
                    troughcolor=color_slider_trough,
                    activebackground=color_red, bg=color_bg)
slider_r.set(0)
slider_r.grid(row=0, column=1, sticky="ns", padx=10)

tk.Label(main_frame, text="Rot\n(Ch 2)", bg=color_bg, fg=color_red,
         font=("Arial", 10, "bold")).grid(row=1, column=1, pady=(10, 5))
lbl_r_val = tk.Label(main_frame, text="0 (0)", bg=color_bg, fg="black",
                     font=("Arial", 10), width=10, anchor="center")
lbl_r_val.grid(row=2, column=1)

# --- 3. Gruen Slider ---
slider_g = tk.Scale(main_frame, **slider_opts,
                    troughcolor=color_slider_trough,
                    activebackground=color_green, bg=color_bg)
slider_g.set(0)
slider_g.grid(row=0, column=2, sticky="ns", padx=10)

tk.Label(main_frame, text="Gruen\n(Ch 3)", bg=color_bg, fg=color_green,
         font=("Arial", 10, "bold")).grid(row=1, column=2, pady=(10, 5))
lbl_g_val = tk.Label(main_frame, text="0 (0)", bg=color_bg, fg="black",
                     font=("Arial", 10), width=10, anchor="center")
lbl_g_val.grid(row=2, column=2)

# --- 4. Blau Slider ---
slider_b = tk.Scale(main_frame, **slider_opts,
                    troughcolor=color_slider_trough,
                    activebackground=color_blue, bg=color_bg)
slider_b.set(0)
slider_b.grid(row=0, column=3, sticky="ns", padx=10)

tk.Label(main_frame, text="Blau\n(Ch 4)", bg=color_bg, fg=color_blue,
         font=("Arial", 10, "bold")).grid(row=1, column=3, pady=(10, 5))
lbl_b_val = tk.Label(main_frame, text="0 (0)", bg=color_bg, fg="black",
                     font=("Arial", 10), width=10, anchor="center")
lbl_b_val.grid(row=2, column=3)

# --- Statuszeile am unteren Rand ---
status_frame = tk.Frame(root, bg=color_slider_trough)
status_frame.pack(side=tk.BOTTOM, fill=tk.X)

lbl_status = tk.Label(status_frame,
                      text=status_text,
                      fg=("#1a7f37" if status_ok else "#c1121f"),
                      bg=color_slider_trough,
                      font=("Arial", 9),
                      anchor="w", padx=10, pady=4)
lbl_status.pack(fill=tk.X)


def on_closing():
    if ser:
        ser.close()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_closing)

# Initialen Zustand berechnen und senden
update_channels()

root.mainloop()
