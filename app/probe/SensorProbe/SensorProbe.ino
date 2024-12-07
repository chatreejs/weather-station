#include <SPI.h>
#include <LoRa.h>
#include <Wire.h>
#include <SoftwareSerial.h>

#define PIN_NSS 10
#define PIN_NRESET 9
#define PIN_IRQ 2
#define PIN_OLED_RESET 4

static const String PROBE_ID = "TH-10-0001";

void setup()
{
  Serial.begin(9600);
  while (!Serial);

  Serial.println("Starting sensor probe");

  // Setup LoRa
  LoRa.setPins(PIN_NSS, PIN_NRESET, PIN_IRQ);

  if (!LoRa.begin(433E6))
  {
    Serial.println("Initialize LoRa failed!");
    while (true)
      ;
  }

  LoRa.setSignalBandwidth(125E3);
  LoRa.setCodingRate4(1);
  LoRa.setSpreadingFactor(10);
  LoRa.setPreambleLength(8);
  LoRa.enableCrc();
  LoRa.setTimeout(100);
  LoRa.setTxPower(2);

  Serial.println("Initialize LoRa succeeded");
  delay(3000);
}

void loop()
{
  float pm25 = random(100, 3000) / 100.0;
  float temp = random(2000, 3000) / 100.0;
  float humidity = random(500, 800) / 100.0;
  String packet = createPacket(pm25, temp, humidity);
  
  LoRa.beginPacket();
  LoRa.print(packet);
  LoRa.endPacket();
  Serial.println("Send packet: " + packet);

  delay(5000);
}

String createPacket(float pm25, float temp, float humidity)
{
  String packet = PROBE_ID + "," + pm25 + "," + temp + "," + humidity;
  return packet;
}