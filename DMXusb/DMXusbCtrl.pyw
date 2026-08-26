#
#   DMXctrl-v2.py - DMX-Fader für USB
#
#   20260711 - Jens & Gemini 3.5 Flash -v1
#   20260711 - Claude Opus 4.8 R & Jens - v2
#
#   FT232 USB zu RS485 Adapter + einfacher LED-Strahler
#   RS485 A -> DMX Pin 3 / Data+
#   RS485 B -> DMX Pin 2 / Data-
#

import tkinter as tk
import serial
import serial.tools.list_ports
import threading
import time


# --- DMX INITIALISIERUNG ---

def find_dmx_port():
    """Erkennung des FTDI-Interface FT232R.
    Gibt (device, info_text) zurück oder (None, info_text)."""
    for port in serial.tools.list_ports.comports():
        # Methode 1: feste USB Hardware-IDs (FT232R: VID=0x0403, PID=0x6001)
        if port.vid == 0x0403 and port.pid == 0x6001:
            return port.device, f"FTDI über Hardware-ID: {port.device}"

        # Methode 2 (Fallback): Textprüfung, falls Windows die IDs verschluckt
        if port.description and ("FT232" in port.description or "FTDI" in port.description):
            return port.device, f"FTDI über Textbeschreibung: {port.device} ({port.description})"

    return None, "Kein FT232R-Interface gefunden."


target_port, port_info = find_dmx_port()

# Status-Text und -Farbe für die GUI vorbereiten
status_text = ""
status_ok = False

try:
    if target_port:
        ser = serial.Serial(
            port=target_port,
            baudrate=250000,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
            timeout=1,
        )
        status_text = f"✓ Interface aktiv – {port_info}"
        status_ok = True
    else:
        ser = None
        status_text = f"⚠ Simulationsmodus – {port_info}"
        status_ok = False
except Exception as e:
    ser = None
    status_text = f"✗ Fehler beim Öffnen des Ports: {e}"
    status_ok = False

# Frame mit 33 Bytes (Index 0 = Start Code, danach 32 DMX-Kanäle)
dmx_data = bytearray(33)
dmx_data[0] = 0x00  # Start Code

running = True


def send_dmx_frame():
    """Sendet kontinuierlich den aktuellen Frame-Zustand im Hintergrund."""
    while running:
        if ser:
            try:
                # 1. BREAK
                ser.break_condition = True
                time.sleep(0.0001)

                # 2. MAB
                ser.break_condition = False
                time.sleep(0.00001)

                # 3. Daten (Start-Byte + 32 Kanäle)
                ser.write(dmx_data)
                ser.flush()
            except Exception as e:
                # Fehler zur Laufzeit in die Statuszeile schreiben (thread-sicher via after)
                update_status(f"✗ Sende-Fehler: {e}", ok=False)

        # Begrenzung auf ca. 40 Frames pro Sekunde
        time.sleep(0.025)


# --- GUI LOGIK ---

def update_status(text, ok):
    """Aktualisiert die Statuszeile thread-sicher."""
    def _apply():
        color = "#1a7f37" if ok else "#c1121f"
        lbl_status.config(text=text, fg=color)
    # Aus Threads heraus GUI nur über after() anfassen
    root.after(0, _apply)


def update_channels(*args):
    """Berechnet die DMX-Werte basierend auf den Slidern und dem Master."""
    master_ratio = slider_master.get() / 255.0

    master_val = max(0, min(255, int(round(slider_master.get()))))
    r_val = max(0, min(255, int(round(slider_r.get() * master_ratio))))
    g_val = max(0, min(255, int(round(slider_g.get() * master_ratio))))
    b_val = max(0, min(255, int(round(slider_b.get() * master_ratio))))

    dmx_data[1] = master_val   # Kanal 1: Gesamt
    dmx_data[2] = r_val        # Kanal 2: Rot
    dmx_data[3] = g_val        # Kanal 3: Grün
    dmx_data[4] = b_val        # Kanal 4: Blau

    lbl_master_val.config(text=f"{master_val}")
    lbl_r_val.config(text=f"{r_val} ({int(round(slider_r.get()))})")
    lbl_g_val.config(text=f"{g_val} ({int(round(slider_g.get()))})")
    lbl_b_val.config(text=f"{b_val} ({int(round(slider_b.get()))})")


# --- ANWENDUNGS-START ---

root = tk.Tk()
root.title("Python DMX RGB Controller")
root.geometry("420x440")

# --- GUI LAYOUT ---
# Farben
color_bg = "#f9f9f9"             # Heller Grauton für das Fenster
color_slider_trough = "#d0d0d0"  # Grauton für den nicht ausgefüllten Bereich
color_master = "#808080"         # Grau für Gesamt
color_red = "#A52A2A"
color_green = "#004B23"
color_blue = "#000080"

root.configure(bg=color_bg)

# Gemeinsame Optionen für alle Slider
slider_opts = {
    'from_': 255,
    'to': 0,
    'orient': tk.VERTICAL,
    'command': update_channels,
    'resolution': 1,        # Nur Ganzzahlen
    'showvalue': False,     # Eigenes Label benutzen
    'width': 25,            # Breite des Schiebers
    'length': 250,          # Länge des Sliders
    'sliderlength': 30,     # Höhe des Schiebers
    'bd': 0,                # Kein Rand
    'highlightthickness': 0 # Kein Fokus-Rand
}

# Haupt-Container
main_frame = tk.Frame(root, bg=color_bg)
main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(20, 5))

# Grid-Konfiguration: Spalten strecken, Slider-Zeile strecken
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

# --- 3. Grün Slider ---
slider_g = tk.Scale(main_frame, **slider_opts,
                    troughcolor=color_slider_trough,
                    activebackground=color_green, bg=color_bg)
slider_g.set(0)
slider_g.grid(row=0, column=2, sticky="ns", padx=10)

tk.Label(main_frame, text="Grün\n(Ch 3)", bg=color_bg, fg=color_green,
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


# Beim Schließen des Fensters Thread beenden
def on_closing():
    global running
    running = False
    dmx_thread.join(timeout=0.5)  # gezielt auf Thread-Ende warten
    if ser:
        ser.close()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_closing)

# Initialen Zustand berechnen (Widgets existieren jetzt)
update_channels()

# Hintergrund-Thread für die DMX-Ausgabe erst jetzt starten
dmx_thread = threading.Thread(target=send_dmx_frame, daemon=True)
dmx_thread.start()

# GUI starten
root.mainloop()
