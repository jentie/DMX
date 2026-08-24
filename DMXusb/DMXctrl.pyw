import tkinter as tk
import serial
import threading
import time

# --- DMX INITIALISIERUNG ---
# Passe den Port ('COM3', '/dev/ttyUSB0' etc.) an deine Umgebung an
try:
    ser = serial.Serial(
        port='COM8',  # UNBEDINGT ANPASSEN!
        baudrate=250000,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_TWO,
        timeout=1
    )
    print("DMX-Interface erfolgreich geöffnet.")
except Exception as e:
    print(f"Fehler beim Öffnen des Ports: {e}")
    print("Das Programm läuft im Simulationsmodus ohne Hardware-Ausgabe.")
    ser = None

# Frame mit 33 Bytes (Index 0 = Start Code, danach 32 DMX-Kanäle)
dmx_data = bytearray(33)
dmx_data[0] = 0x00  # Start Code

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
                print(f"Sende-Fehler: {e}")
        
        # Begrenzung auf ca. 40 Frames pro Sekunde
        time.sleep(0.025)

# --- GUI LOGIK ---
def update_channels(*args):
    """Berechnet die DMX-Werte basierend auf den Slidern und dem Master."""
    # Sicherheitsabfrage: Prüfen, ob die kritischen GUI-Elemente bereits existieren
    try:
        # Wir prüfen, ob die Variablen im globalen Namensraum existieren und nicht None sind
        if 'slider_master' not in globals() or 'slider_r' not in globals() or \
           'slider_g' not in globals() or 'slider_b' not in globals() or \
           'lbl_b_val' not in globals():
            return
        
        # Zusätzlich prüfen wir, ob die Tkinter-Widgets tatsächlich initialisiert wurden
        if slider_master is None or slider_r is None or slider_g is None or \
           slider_b is None or lbl_b_val is None:
            return
            
    except NameError:
        # Falls eine der Variablen noch komplett unbekannt ist, fangen wir das hier ab
        return

    master = slider_master.get() / 255.0  # Normieren auf 0.0 bis 1.0
    
    # Werte runden und strikt auf den Bereich 0-255 begrenzen
    master_val = max(0, min(255, int(round(slider_master.get()))))
    r_val = max(0, min(255, int(round(slider_r.get() * master))))
    g_val = max(0, min(255, int(round(slider_g.get() * master))))
    b_val = max(0, min(255, int(round(slider_b.get() * master))))
    
    # DMX-Array sicher aktualisieren
    dmx_data[1] = master_val               # Kanal 1: Gesamt
    dmx_data[2] = r_val                    # Kanal 2: Rot
    dmx_data[3] = g_val                    # Kanal 3: Grün
    dmx_data[4] = b_val                    # Kanal 4: Blau
    
    # Labels in der GUI aktualisieren
    lbl_master_val.config(text=f"{master_val}")
    lbl_r_val.config(text=f"{r_val} ({int(round(slider_r.get()))})")
    lbl_g_val.config(text=f"{g_val} ({int(round(slider_g.get()))})")
    lbl_b_val.config(text=f"{b_val} ({int(round(slider_b.get()))})")

# --- ANWENDUNGS-START ---
root = tk.Tk()
root.title("Python DMX RGB Controller")
root.geometry("420x400")

# Hintergrund-Thread für die DMX-Ausgabe starten
running = True
dmx_thread = threading.Thread(target=send_dmx_frame, daemon=True)
dmx_thread.start()

# --- GUI LAYOUT ---
# Wir benutzen hier die klassischen tk.Scale, da sie sich einfacher färben lassen
# Definition der Farben
color_bg = "#f9f9f9"  # Heller Grauton für das Fenster
color_slider_trough = "#d0d0d0" # Grauton für den nicht ausgefüllten Bereich
color_master = "#808080" # Grau für Gesamt
color_red = "#A52A2A"    # Helles Rot
color_green = "#004B23"  # Tannengrün
color_blue = "#000080"   # Helles Blau

root.configure(bg=color_bg)

# Gemeinsame Optionen für alle Slider
slider_opts = {
    'from_': 255,
    'to': 0,
    'orient': tk.VERTICAL,
    'command': update_channels,
    'resolution': 1,       # Nur Ganzzahlen
    'showvalue': False,    # Eigenes Label benutzen
    'width': 25,           # Breite des Schiebers
    'length': 250,         # Länge des Sliders
    'sliderlength': 30,    # Höhe des Schiebers
    'bd': 0,               # Kein Rand
    'highlightthickness': 0 # Kein Fokus-Rand
}

# Haupt-Container
main_frame = tk.Frame(root, bg=color_bg)
main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
main_frame.pack(fill=tk.BOTH, expand=True)

# Grid-Konfiguration
for i in range(4):
    main_frame.columnconfigure(i, weight=1)

# --- 1. Master Slider (Gesamt) ---
slider_master = tk.Scale(main_frame, **slider_opts, 
                         troughcolor=color_slider_trough,
                         activebackground=color_master,
                         bg=color_bg)
slider_master.set(255)
slider_master.grid(row=0, column=0, sticky="ns", padx=10)

tk.Label(main_frame, text="Gesamt\n(Ch 1)", bg=color_bg, fg="black", font=("Arial", 10, "bold")).grid(row=1, column=0, pady=(10, 5))
lbl_master_val = tk.Label(main_frame, text="255", bg=color_bg, fg="black", font=("Arial", 10), width=10, anchor="center")
lbl_master_val.grid(row=2, column=0)

# --- 2. Rot Slider ---
slider_r = tk.Scale(main_frame, **slider_opts,
                   troughcolor=color_slider_trough,
                   activebackground=color_red,
                   bg=color_bg)
slider_r.set(0)
slider_r.grid(row=0, column=1, sticky="ns", padx=10)

tk.Label(main_frame, text="Rot\n(Ch 2)", bg=color_bg, fg=color_red, font=("Arial", 10, "bold")).grid(row=1, column=1, pady=(10, 5))
lbl_r_val = tk.Label(main_frame, text="0 (0)", bg=color_bg, fg="black", font=("Arial", 10), width=10, anchor="center")
lbl_r_val.grid(row=2, column=1)

# --- 3. Grün Slider ---
slider_g = tk.Scale(main_frame, **slider_opts,
                   troughcolor=color_slider_trough,
                   activebackground=color_green,
                   bg=color_bg)
slider_g.set(0)
slider_g.grid(row=0, column=2, sticky="ns", padx=10)

tk.Label(main_frame, text="Grün\n(Ch 3)", bg=color_bg, fg=color_green, font=("Arial", 10, "bold")).grid(row=1, column=2, pady=(10, 5))
lbl_g_val = tk.Label(main_frame, text="0 (0)", bg=color_bg, fg="black", font=("Arial", 10), width=10, anchor="center")
lbl_g_val.grid(row=2, column=2)

# --- 4. Blau Slider ---
slider_b = tk.Scale(main_frame, **slider_opts,
                   troughcolor=color_slider_trough,
                   activebackground=color_blue,
                   bg=color_bg)
slider_b.set(0)
slider_b.grid(row=0, column=3, sticky="ns", padx=10)

tk.Label(main_frame, text="Blau\n(Ch 4)", bg=color_bg, fg=color_blue, font=("Arial", 10, "bold")).grid(row=1, column=3, pady=(10, 5))
lbl_b_val = tk.Label(main_frame, text="0 (0)", bg=color_bg, fg="black", font=("Arial", 10), width=10, anchor="center")
lbl_b_val.grid(row=2, column=3)

# Zeile 0 soll sich strecken
main_frame.rowconfigure(0, weight=1)

# Beim Schließen des Fensters Thread beenden
def on_closing():
    global running
    running = False
    time.sleep(0.1) # Dem Thread Zeit geben zu stoppen
    if ser:
        ser.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Initialen Zustand berechnen
update_channels()

# GUI starten
root.mainloop()
