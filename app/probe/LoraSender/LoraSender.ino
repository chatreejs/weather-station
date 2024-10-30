#include <SPI.h>
#include <LoRa.h>
#include <Wire.h>

int counter = 0;

// LoRa connect config
#define NSS_PIN 10
#define NRESET_PIN 9
#define DIO0_PIN 8

void setup() {
  Serial.begin(9600);
  while (!Serial)
    ;

  Serial.println("LoRa Node - Sender #1");

  LoRa.setPins(NSS_PIN, NRESET_PIN, DIO0_PIN);
  if (!LoRa.begin(433E6)) {
    Serial.println("LoRa init failed!");
    while (true)
      ;
  }
  
  // LoRa.setSignalBandwidth(125E3);
  // LoRa.setCodingRate4(1);
  // LoRa.setSpreadingFactor(12);
  // LoRa.setPreambleLength(8);
  // LoRa.enableCrc();
  // LoRa.setTimeout(100);
  // LoRa.setTxPower(17);

  Serial.println("LoRa init succeeded.");
}

void loop() {
  Serial.print("Sending packet: ");
  Serial.println(counter);

  // send packet
  LoRa.beginPacket();
  LoRa.print("Hello #");
  LoRa.print(counter);
  LoRa.endPacket();
  
  counter++;

  delay(5000);
}