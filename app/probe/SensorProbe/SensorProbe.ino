#include <SPI.h>
#include <LoRa.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <SoftwareSerial.h>

#define PIN_NSS 10
#define PIN_NRESET 9
#define PIN_DIO0 8
#define PIN_OLED_RESET 4

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

static const String PROBE_ID = "TH-10-0001";

// static const uint8_t PIN_UART_RX = 10;
// static const uint8_t PIN_UART_TX = 11;

Adafruit_SSD1306 display(PIN_OLED_RESET);
// SoftwareSerial sensorSerial(PIN_UART_RX, PIN_UART_TX);

void setup() {
  Serial.begin(9600);
  // sensorSerial.begin(115200);

  Serial.println("Starting sensor probe");
  display.begin(SSD1306_SWITCHCAPVCC, 0x3c);
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);
  display.println("Sensor Probe v1.0.0");
  display.print("Probe ID : ");
  display.println(PROBE_ID);
  display.display();

  while (!Serial)
    ;

  // Setup LoRa
  LoRa.setPins(PIN_NSS, PIN_NRESET, PIN_DIO0);

  if (!LoRa.begin(433E6)) {
    Serial.println("Initialize LoRa failed!");
    display.println("0x01 - ERR_LORA_INIT");
    display.display();
    while (true)
      ;
  }

  display.print("Freq : ");
  display.println("433MHz");
  display.display();

  LoRa.setSignalBandwidth(125E3);
  LoRa.setCodingRate4(1);
  LoRa.setSpreadingFactor(12);
  LoRa.setPreambleLength(8);
  LoRa.enableCrc();
  LoRa.setTimeout(100);
  LoRa.setTxPower(17);

  Serial.println("Initialize LoRa succeeded");
  display.println("0x00 - SUCCESS");
  display.display();
  delay(3000);
}

void loop() {
  // if (sensorSerial.available()) {
  //   Serial.println("Sensor connected");
  // }
  float value = random(1, 500) / 100.0;
  String packet = createPacket("pm25", value);

  display.clearDisplay();
  display.setCursor(0, 0);
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.print(packet);
  display.display();

  LoRa.beginPacket();
  LoRa.print(packet);
  LoRa.endPacket();
  Serial.print("Send LoRa packet: ");
  Serial.println(packet);
}

String createPacket(String type, float value) {
  String packet = PROBE_ID + "," + type + "," + value;
  return packet;
}