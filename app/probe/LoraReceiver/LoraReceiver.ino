#include <SPI.h>
#include <LoRa.h>

// LoRa connect config
#define NSS_PIN    10
#define NRESET_PIN 9
#define DIO0_PIN   8

void setup() {
  pinMode(6, OUTPUT);
  Serial.begin(9600);
  while (!Serial);

  Serial.println("LoRa Node - Receiver");
  LoRa.setPins(NSS_PIN, NRESET_PIN, DIO0_PIN);

  if (!LoRa.begin(433E6)) {
    Serial.println("LoRa init failed!");
    while(true);
  }

  LoRa.setSignalBandwidth(125E3);
  LoRa.setCodingRate4(1);
  LoRa.setSpreadingFactor(12);
  LoRa.setPreambleLength(8);
  LoRa.enableCrc();
  LoRa.setTimeout(100);
  LoRa.setTxPower(17);

  Serial.println("LoRa init succeeded.");
}

void loop() {
  if (LoRa.parsePacket() > 0) {
    String text = LoRa.readString();
    Serial.print("Receive packet:");
    Serial.print("'" + text + "'");
    Serial.print(" RSSI:");
    Serial.print(LoRa.packetRssi());
    Serial.print(" SNR:");
    Serial.println(LoRa.packetSnr());
    digitalWrite(6, LOW);
    delay(100);
    digitalWrite(6, HIGH);
  }
  delay(1);
}