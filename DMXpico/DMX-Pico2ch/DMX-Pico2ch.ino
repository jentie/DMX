/*
    DMX-Pico2ch - send & receive DMX frames

    2026-07-26, Jens mit Claude

    send DMX frames
    - update via USB with channel-value-pair (hex)

    receicve DMX frames
    - decoded to hex via USB, 2 samples per second 

*/


#include <DmxOutput.h>
#include <DmxInput.h>


// ---------- Konfiguration ----------
const uint    TX_PIN        = 0;     // GP0 = Kanal 0 Tx (Ausgabe)
const uint    RX_PIN        = 5;     // GP5 = Kanal 1 Rx (Empfang)
//const uint16_t SAMPLE_COUNT = 128;   // wie viele Kanaele an PC senden
const uint16_t SAMPLE_COUNT = 512;   // wie viele Kanaele an PC senden
const uint32_t SAMPLE_PERIOD_MS = 500;  // 2x pro Sekunde
const uint32_t TX_PERIOD_MS = 25;    // ~40 DMX-Frames/s ausgeben

DmxOutput dmxOut;
DmxInput  dmxIn;

// ---------- Puffer ----------
uint8_t txUniverse[513];                              // 0 = Startcode
volatile uint8_t rxUniverse[DMXINPUT_BUFFER_SIZE(0, 512)];

// ---------- Empfangs-Parser (PC -> Pico) ----------
char    lineBuf[32];
uint8_t lineLen = 0;

void applyPair(uint16_t ch, uint8_t val) {
  if (ch >= 1 && ch <= 512) {
    txUniverse[ch] = val;
  }
}

// Erwartet "KANAL,WERT" beide hexadezimal, z.B. "0A,FF"
void parseLine(const char *s) {
  unsigned int ch, val;
  if (sscanf(s, "%x,%x", &ch, &val) == 2) {
    if (val > 0xFF) val = 0xFF;
    applyPair((uint16_t)ch, (uint8_t)val);
  }
}

void pollSerialInput() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (lineLen > 0) {
        lineBuf[lineLen] = '\0';
        parseLine(lineBuf);
        lineLen = 0;
      }
    } else if (lineLen < sizeof(lineBuf) - 1) {
      lineBuf[lineLen++] = c;
    } else {
      lineLen = 0;   // Ueberlauf -> verwerfen
    }
  }
}

// ---------- Sampling (Pico -> PC), Hex-codiert ----------
void printHexByte(uint8_t b) {
  if (b < 0x10) Serial.print('0');   // fuehrende Null
  Serial.print(b, HEX);
}

void sendSampleToPC() {
  Serial.print("DMX:");
  for (uint16_t ch = 1; ch <= SAMPLE_COUNT; ch++) {
    printHexByte(rxUniverse[ch]);
    if (ch < SAMPLE_COUNT) Serial.print(',');
  }
  Serial.println();
}

// ---------- Setup ----------
void setup() {
  Serial.begin(115200);

  dmxOut.begin(TX_PIN);
  txUniverse[0] = 0;                 // Startcode

  dmxIn.begin(RX_PIN, 1, 512);       // Startkanal 1, 512 Kanaele
  dmxIn.read_async(rxUniverse);      // laeuft im Hintergrund (PIO/DMA)
}

// ---------- Loop ----------
void loop() {
  static uint32_t lastTx = 0;
  static uint32_t lastSample = 0;

  pollSerialInput();                 // PC-Befehle einlesen

  if (millis() - lastTx >= TX_PERIOD_MS) {   // DMX ausgeben
    lastTx = millis();
    if (!dmxOut.busy()) {
      dmxOut.write(txUniverse, 513);
    }
  }

  if (millis() - lastSample >= SAMPLE_PERIOD_MS) {  // Sampling an PC
    lastSample = millis();
    sendSampleToPC();
  }
}
