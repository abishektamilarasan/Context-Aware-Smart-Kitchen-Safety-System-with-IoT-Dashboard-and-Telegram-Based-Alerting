# Smart Kitchen Monitoring System 🍳🔒

A complete, dual-microcontroller smart kitchen safety and telemetry system. This project uses a **Raspberry Pi Pico** to execute hard real-time safety logic (sensor polling, thermal shutdown, gas leak detection) and an **ESP8266** acting as a Wi-Fi bridge to serve a sleek, interactive Web Dashboard.

## ✨ Features
* **Live Telemetry Dashboard:** Real-time updates for Gas (PPM), Temperature (°C), Humidity (%), Flame Detection, and Motion Detection.
* **Intelligent Auto-Release Overrides:** Full manual authority over the Fan, Buzzer, and LEDs from the web interface. Once an active crisis (like a gas leak) clears, the system dynamically drops the manual locks and reverts to automated protection mode.
* **Thermal & Gas Lockdown:** If temperature exceeds the threshold or gas levels spike, the system aggressively locks down by forcing a Servo to shut off the physical gas valve, blasting the siren, and spinning up the exhaust fan.
* **DHT11 Integration:** Native support for the digital DHT11 sensor for stable ambient kitchen temperature and humidity tracking.
* **Hardware Panic Button:** A physical push-button to override lockdowns natively.

---

## 🔌 Hardware Wiring Guide

### 1. Raspberry Pi Pico (The Core Brain)
This board handles all physical hardware interactions and mathematical safety triggers. Ensure you wire these exactly as specified in the updated `main.py`:

| Component | Pico Pin | Type / Notes |
| :--- | :--- | :--- |
| **DHT11 Temp/Hum Sensor** | `GP15` | Digital Input (Data pin) |
| **MQ2 Gas Sensor** | `GP26` (ADC0) | Analog Input |
| **Flame Sensor** | `GP14` | Digital Input |
| **PIR Motion Sensor** | `GP13` | Digital Input |
| **Physical Button** | `GP16` | Digital Input (Pull-Up) |
| **Alarm Buzzer** | `GP12` | Digital Output |
| **Exhaust Fan Relay** | `GP11` | Digital Output |
| **Servo Motor (Valve)**| `GP10` | PWM Output (50Hz) |
| **Alert LED (Red)** | `GP17` | Digital Output |
| **Motion LED (Green)** | `GP18` | Digital Output |
| **UART TX (To ESP8266)**| `GP8`  | Connects to ESP8266 `RX` pin |
| **UART RX (From ESP8266)**| `GP9`  | Connects to ESP8266 `TX` pin |

> **⚠️ CRITICAL:** You **must** connect a Ground (GND) pin from the Raspberry Pi Pico to a Ground (GND) pin on the ESP8266 so they share a common electrical reference line!

### 2. ESP8266 NodeMCU (The Wi-Fi Bridge)
This board solely acts as a wireless HTTP server. It blindly bridges the web dashboard JSON commands to the Pi Pico via a high-speed UART hardware serial line.

* **RX Pin:** Connect to Pico `GP8`
* **TX Pin:** Connect to Pico `GP9`
* **GND:** Connect to Pico `GND`

---

## 🚀 Installation & Setup

### Step 1: Program the Raspberry Pi Pico
1. Install **MicroPython** onto your Raspberry Pi Pico.
2. Open Thonny IDE.
3. Upload `main.py` to the root directory of the Pico.
4. The Pico will automatically begin running the hardware loops and parsing the DHT11 data!

### Step 2: Program the ESP8266
1. Open the Arduino IDE.
2. Open `esp8266_bridge.ino`.
3. Change the Wi-Fi configuration lines at the top of the file to match your home network:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
4. Flash the code to the ESP8266.
5. Open the Arduino Serial Monitor (115200 baud). Once connected to your Wi-Fi, it will print an IP address (e.g., `192.168.1.50`). Save this IP address!

### Step 3: Launch the Dashboard
1. Simply double-click the `index.html` file on your computer or host it on a local lightweight web server.
2. At the top right of the beautiful dark-mode interface, enter the **ESP8266 IP Address** you got from Step 2 into the connection bar.
3. Click **Connect**.
4. The dot will turn glowing green, and your live kitchen telemetry (including your new DHT11 Temp and Humidity) will instantly spring to life!

---

## 🛠️ Built With
* **MicroPython** (Raspberry Pi Pico Logic)
* **C++ / Arduino Core** (ESP8266 Web Server)
* **Vanilla HTML/CSS/JS** (Dashboard UI)
* **Lucide Icons** (Premium SVG Icons)
