**🚀 Turning the Heart of the Home into a Smart, Safe Haven! 🍳🔥**

I’m thrilled to share the latest IoT project I developed a **Comprehensive Smart Kitchen Automation System**. 

Kitchens are notorious for safety hazards—gas leaks, forgotten stovetops, and unattended flames. We wanted to build a localized, robust system that not only monitors the kitchen environment in real-time but *acts* autonomously to prevent disasters. 

Here’s a deep dive into how we built it and how it works:

### 🧠 Dual-Microcontroller Architecture
To ensure rock-solid performance, we split the processing responsibilities:
🔹 **Raspberry Pi Pico (The Brains):** Handles all the core, non-blocking hardware logic. It reads sensor data, manages safety timeout loops, and locally triggers hardware interventions without relying on internet connectivity.
🔹 **ESP8266 NodeMCU (The Network Bridge):** Acts as a dedicated WiFi-to-UART bridge. It handles all WebSocket traffic, serves data to the local dashboard, and manages outbound API calls. 

### ⚙️ Core Workflow & Safety Features
1️⃣ **Real-Time Sensor Fusion:** The system continuously monitors temperature & humidity (DHT11), combustible gases & smoke (MQ2), and localized motion (PIR).
2️⃣ **Interactive Web Dashboard:** A sleek, responsive web interface presents live telemetry data, allows users to set dynamic temperature/gas thresholds, and provides manual override buttons for the kitchen hardware (like exhaust fans).
3️⃣ **Automated Gas Shut-Off:** If the MQ2 sensor detects a gas leak or flame, the Pico instantly triggers a Servo Motor to physically rotate and shut off the gas regulator—stopping the problem at the source.
4️⃣ **Smart Cooking Timer & 10-Min Rule:** Started a pot on the stove and forgot about it? A built-in cooking timer can auto-shutoff the gas when time is up. Additionally, if the stove is on but the PIR sensor detects no motion for 10 minutes (unattended stove), the system safely shuts down automatically.
5️⃣ **Child Protection Mode:** When armed via the dashboard, any motion detected by the PIR sensor triggers a loud local buzzer alarm, deterring kids from a hot stovetop.

### 📱 Instant Telegram Alerts
Because you aren't always looking at a dashboard, critical events shouldn't go unnoticed. The ESP8266 instantly pushes alerts directly to our phones via a **Telegram Bot** if:
🚨 Gas levels exceed safe thresholds.
🚨 A flame is detected.
🚨 The stove was left unattended and auto-triggered a safety shutdown.

**🛠 Tech Stack:** C++ / Arduino IDE, MicroPython, HTML/CSS/JS (Vanilla WebSockets), Telegram API.

Building this pushed our team to handle complex asynchronous communication (UART), real-time web bridging, and physical hardware actuations (servo kinematics). The peace of mind knowing the kitchen can handle its own emergencies? Priceless. 🧠💡
