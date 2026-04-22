#include <ESP8266WiFi.h>
#include <WebSocketsServer.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecure.h>


const char* WIFI_SSID = "wifi name";
const char* WIFI_PASS = "password";

const char* BOT_TOKEN = "bot token, create it in the telegram";
const char* CHAT_ID   = "your chat id";

// Using Hardware Serial (TX/RX pins) for Pico communication at 9600 baud.
// Remember to unplug Pico when uploading code via USB!

WebSocketsServer webSocket(81);
String lastAlert = "";


void sendTelegram(String message) {
    WiFiClientSecure client;
    client.setInsecure();

    HTTPClient http;
    http.setTimeout(5000);  

    String url = "https://api.telegram.org/bot" + String(BOT_TOKEN) + "/sendMessage";

    Serial.println("Sending Telegram message...");

    if (http.begin(client, url)) {
        http.addHeader("Content-Type", "application/json");

        String body = "{\"chat_id\":\"" + String(CHAT_ID) + "\",\"text\":\"" + message + "\"}";
        
        int code = http.POST(body);

        Serial.print("HTTP Response code: ");
        Serial.println(code);

        String response = http.getString();
        Serial.println("Response: " + response);

        http.end();
    } else {
        Serial.println("HTTP begin failed");
    }
}


void webSocketEvent(uint8_t num, WStype_t type, uint8_t *payload, size_t length) {
    switch (type) {
        case WStype_TEXT: {
            String cmd = "";
            for (size_t i = 0; i < length; i++) {
                cmd += (char)payload[i];
            }
            cmd.trim();
            Serial.println(cmd);
            break;
        }
    }
}

//  SETUP
void setup() {
    Serial.begin(9600);
    delay(10);
    
    Serial.println("\n\n--- Smart Kitchen ESP8266 Started ---");

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    
    Serial.print("Connecting to WiFi...");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    
    Serial.println("\n=====================================");
    Serial.println("CONNECTED! YOUR ESP8266 IP ADDRESS IS:");
    Serial.println(WiFi.localIP());
    Serial.println("=====================================");
    Serial.println("Now communicating with Pico...");
    
    //       Telegram will be tested when a real alert triggers

    webSocket.begin();
    webSocket.onEvent(webSocketEvent);
}

//  LOOP
void loop() {
    webSocket.loop();

    if (Serial.available()) {
        String line = Serial.readStringUntil('\n');
        line.trim();
        Serial.println("Received"+line);
        if (line.length() > 2) {
            webSocket.broadcastTXT(line);

            // Telegram alerts (plain ASCII — no emojis to avoid encoding issues)
            if (line.indexOf("GAS_HIGH") > -1 ) {
                lastAlert = "GAS_HIGH";
                sendTelegram("[ALERT] Gas level exceeded threshold!");
            } else if (line.indexOf("FLAME") > -1 ) {
                lastAlert = "FLAME";
                sendTelegram("[ALERT] Flame detected! Gas valve closed!");
            } else if (line.indexOf("UNATTENDED") > -1 ) {
                lastAlert = "UNATTENDED";
                sendTelegram("[ALERT] Stove unattended for 10 min - system shut down!");
            } else if (line.indexOf("\"al\":\"\"") > -1) {
                lastAlert = "";
            }
        }
    }
}
