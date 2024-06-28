
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLEClient.h>
#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>
#include <SoftwareSerial.h>

#define SERVICE_UUID        "f10016f6-542b-460a-ac8b-bbb0b2010597"
#define CHARACTERISTIC_UUID "f22535de-5375-44bd-8ca9-d0ea9ff9e410"
#define CURRENTSENSING_UUID "640b8bf5-3c88-44f6-95e0-f5813b390d78"
BLECharacteristic *csCharacteristic;

bool deviceConnected = false;

//Adafruit_NeoPixel strip(1, 0 , NEO_GRB + NEO_KHZ800);

//const int subchain_pins[6] = {26,25,5,19,21,14,32,15,33,27,12,13};
const int subchain_pins[8] = {26, 25, 5, 19, 21, 14, 32, 15};
const int subchain_num = 8;
uint32_t colors[5];
int color_num = 5;

EspSoftwareSerial::UART serial_group[12];

const int maxJsonCount = 7; // Maximum number of JSON objects you expect
/*
   this function takes in a String that contains multiple JSONs, split them by '\n', and return the String array
*/
String* splitJsons(const String& jsonString) {
  String* jsonArray = new String[maxJsonCount];
  int startIndex = 0;
  int endIndex = 0;
  int jsonCount = 0; // Counter for the number of JSON objects found

  while (startIndex < jsonString.length()) {
    // Find the end index of the JSON object
    endIndex = jsonString.indexOf('\n', startIndex);
    if (endIndex == -1) {
      endIndex = jsonString.length();
    }

    // Extract the JSON object and store it in the array
    String json = jsonString.substring(startIndex, endIndex);
    jsonArray[jsonCount] = json;

    // Move to the next JSON object
    jsonCount++;
    startIndex = endIndex + 1;

    // Break if the maximum number of JSON objects has been reached
    if (jsonCount >= maxJsonCount) {
      break;
    }
  }

  return jsonArray;
}

class MyCharacteristicCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
      // get command
      std::string value = pCharacteristic->getValue();
      String value_str = value.c_str();
      Serial.print(millis());
      Serial.print("receive data = ");
      Serial.println(value_str);
      // split the receive data into JSONs
      String* jsonArray = splitJsons(value_str);
//      Serial.print(millis());
//      Serial.println("finish splitjson");
      // decode JSON
      for (int i = 0; i < maxJsonCount; i++) {
        if (!jsonArray[i].isEmpty()) {
//          Serial.println(jsonArray[i]);
          DynamicJsonDocument command(1024);
          deserializeJson(command, jsonArray[i]);
//          Serial.print(millis());
//          Serial.println("finish deserialize");
          sendCommand(command);
//          Serial.print(millis());
//          Serial.println("finish sendcommand");
        }
      }
    }

    /* command format
        command = {
            'addr':motor_addr,
            'mode':start_or_stop,
            'duty':3, # default
            'freq':2, # default
            'wave':0, # default
        }
    */
    void sendCommand(DynamicJsonDocument& command) {
      int motor_addr = command["addr"].as<int>();
      int send_motor_addr = motor_addr % 30;
      int serial_group_number = motor_addr / 30;
      int is_start = command["mode"].as<int>();
      int duty = command["duty"].as<int>();
      int freq = command["freq"].as<int>();
      int wave = command["wave"].as<int>();
      if (motor_addr >= 0 && motor_addr < 256) { // maximum number of motor on one chain
        if (is_start == 1) { //start command, two bytes
          uint8_t message[2];
          message[0] = ((send_motor_addr) << 1) + is_start;
          message[1] = 128 + (duty << 3) + (freq << 1) + wave;
          serial_group[serial_group_number].write(message, 2);
          //          Serial.println(serial_group_number);
          //          Serial.println(send_motor_addr);
          //          Serial.println(message[1]);
          //          strip.setPixelColor(0, colors[motor_addr % color_num]);
          //          strip.show();
        }
        else { //stop command, only one byte
          uint8_t message = (send_motor_addr << 1) + is_start;
          serial_group[serial_group_number].write(message);
          //          strip.setPixelColor(0, 0, 0, 0);
          //          strip.show();
        }
      }
      else {
        Serial.println("motor address is not in range...");
      }
    }
};

class MyServerCallbacks: public BLEServerCallbacks {
//    void onConnect(BLEServer* pServer, ) {
//      Serial.println("connected!");
//      std::map<uint16_t, conn_status_t> peerDevices = pServer->getPeerDevices(false);
//      Serial.println(peerDevices.size());
//      conn_status_t deviceConn = peerDevices[0];
//      Serial.println(sizeof(void*));
//      Serial.println(uint32_t(deviceConn.peer_device));
//      Serial.println(deviceConn.connected);
//      Serial.println(deviceConn.mtu);
//      BLEClient *client = (BLEClient*)deviceConn.peer_device;
//      Serial.println(client->getPeerAddress().toString().c_str());
//      Serial.println(BLEDevice::toString().c_str());
//      deviceConnected = true;
//    };
    void onConnect(BLEServer* pServer, esp_ble_gatts_cb_param_t *param){
        Serial.println("connected!");
        Serial.println(BLEDevice::toString().c_str());
        char bda_str[18];
        sprintf(bda_str, "%02X:%02X:%02X:%02X:%02X:%02X", param->connect.remote_bda[0], param->connect.remote_bda[1], param->connect.remote_bda[2], param->connect.remote_bda[3], param->connect.remote_bda[4], param->connect.remote_bda[5]);
        Serial.println("Device connected with Address: " + String(bda_str));
        pServer->updateConnParams(param->connect.remote_bda, 0, 0, 0, 100);
        deviceConnected = true;
    }

    void onDisconnect(BLEServer* pServer) {
      Serial.println("disconnected!");
      delay(500);
      deviceConnected = false;
      BLEDevice::startAdvertising();
    }
};


void setup() {
  Serial.begin(115200);//even parity check
  //  pinMode(8, OUTPUT);
  //  pinMode(7, INPUT);
  //  Serial1.begin(115200, SERIAL_8E1);// Hardware Serial
  Serial.print("number of hardware serial available: ");
  Serial.println(SOC_UART_NUM);
  for (int i = 0; i < subchain_num; ++i) {
    Serial.print("initialize uart on ");
    Serial.println(subchain_pins[i]);
    serial_group[i].begin(115200, SWSERIAL_8E1, -1, subchain_pins[i], false);
    serial_group[i].enableIntTx(false);
    if (!serial_group[i]) { // If the object did not initialize, then its configuration is invalid
      Serial.println("Invalid EspSoftwareSerial pin configuration, check config");
    }
    delay(200);
  }
  Serial.println("Starting BLE work!");

  //setup LED
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);
  pinMode(2, OUTPUT);
  digitalWrite(2, HIGH);
  //  strip.begin();
  //  strip.setBrightness(64);
  //  colors[0] = strip.Color(255, 0, 0);
  //  colors[1] = strip.Color(0, 255, 0);
  //  colors[2] = strip.Color(0, 0, 255);
  //  colors[3] = strip.Color(255, 0, 255);
  //  colors[4] = strip.Color(255, 255, 0);
  //  strip.setPixelColor(0, colors[0]);
  //  strip.show();

  //BLE setup
  BLEDevice::init("FEATHER_ESP32");
  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());
  BLEService *pService = pServer->createService(SERVICE_UUID);
  BLECharacteristic *pCharacteristic = pService->createCharacteristic(
                                         CHARACTERISTIC_UUID,
                                         BLECharacteristic::PROPERTY_READ |
                                         BLECharacteristic::PROPERTY_WRITE
                                       );
  pCharacteristic->setValue("0");
  pCharacteristic->setCallbacks(new MyCharacteristicCallbacks());
//  csCharacteristic = pService->createCharacteristic(
//                       CURRENTSENSING_UUID,
//                       BLECharacteristic::PROPERTY_READ
//                     );
//  csCharacteristic->setValue("0");

  pService->start();

  // BLEAdvertising *pAdvertising = pServer->getAdvertising();  // this still is working for backward compatibility
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinPreferred(0x00);
  pAdvertising->setMaxPreferred(0x00);
  BLEDevice::startAdvertising();
  Serial.println("Characteristic defined! Now you can read it in your phone!");

  //actuator pin setup
  //  for (int i=0; i<subchain_num; ++i){
  //    pinMode(subchain_pins[i], OUTPUT);
  //    digitalWrite(subchain_pins[i], LOW);
  //  }
//  pinMode(39, INPUT);
}

void loop() {
  // put your main code here, to run repeatedly:
//  csCharacteristic->setValue(String(analogRead(39)).c_str());
  delay(1000);
}
