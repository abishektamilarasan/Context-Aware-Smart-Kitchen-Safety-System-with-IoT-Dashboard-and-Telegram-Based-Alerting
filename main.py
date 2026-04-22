import machine, dht, time, json


DHT_PIN     = 15
GAS_PIN     = 26        # ADC0
FLAME_PIN   = 14
PIR_PIN     = 13
BTN_PIN     = 16
BUZZER_PIN  = 12
RELAY_PIN   = 11        # Exhaust fan
SERVO_PIN   = 10
ALERT_LED   = 17        # Red LED — blinks during alerts
MOTION_LED  = 18        # Green LED — ON when motion detected
UART_TX     = 8
UART_RX     = 9

#  INIT PERIPHERALS 
dht_s   = dht.DHT11(machine.Pin(DHT_PIN))
gas_adc = machine.ADC(machine.Pin(GAS_PIN))
flame_p = machine.Pin(FLAME_PIN, machine.Pin.IN)
pir_p   = machine.Pin(PIR_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)
btn_p   = machine.Pin(BTN_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
buz_p   = machine.Pin(BUZZER_PIN, machine.Pin.OUT)
fan_p   = machine.Pin(RELAY_PIN, machine.Pin.OUT)
srv     = machine.PWM(machine.Pin(SERVO_PIN))
srv.freq(50)
alert_led = machine.Pin(ALERT_LED, machine.Pin.OUT)
mot_led   = machine.Pin(MOTION_LED, machine.Pin.OUT)
uart    = machine.UART(0, baudrate=9600,
                       tx=machine.Pin(UART_TX),
                       rx=machine.Pin(UART_RX),
                       timeout=50)

#  STATE
temp = 0.0
hum  = 0.0              # humidity %
gas  = 0
flm  = False            # flame detected
mot  = False            # motion detected

fan_on  = False
buz_on  = False
vlv_open = False        # servo valve: False=closed(0°) True=open(90°)

gas_thr  = 6000         # gas PPM threshold
temp_thr = 50           # temperature °C threshold

cook_tmr      = 0       # cooking timer (seconds)
last_tmr_tick = 0

last_mot_ms    = time.ticks_ms()
UNATTEND_MS    = 600000  # 10 min
unattend_flag  = False

prev_btn    = 1
prev_btn_ms = 0
DEBOUNCE    = 200

last_alert_ms = 0
ALERT_COOL    = 30000

last_read  = 0
last_dht_ms = 0          # DHT11 needs 2s between reads
last_send  = 0
INTERVAL   = 1000

alert_blink_ms = 0      # for blinking the alert LED
pending_alert  = ""     # stores alert until sent to ESP

#  HELPERS 
def servo_angle(a):
    """Move servo to angle 'a' (0-180). Uses standard SG90 pulse widths."""
    # SG90 at 50Hz: 0.5ms=0°, 1.5ms=90°, 2.5ms=180°
    # duty_u16 range: ~1640 (0.5ms) to ~8200 (2.5ms)
    duty = int(1640 + (a / 180) * (8200 - 1640))
    srv.duty_u16(duty)
    time.sleep_ms(300)   # give servo time to physically move

def set_fan(on):
    global fan_on
    fan_on = on
    fan_p.value(1 if on else 0)

def set_buz(on):
    global buz_on
    buz_on = on
    buz_p.value(1 if on else 0)

def set_valve(opened):
    global vlv_open
    if vlv_open == opened:
        return                    # already in desired state, skip
    vlv_open = opened
    servo_angle(90 if opened else 0)

def read_sensors():
    global temp, hum, gas, flm, mot, last_dht_ms
    now = time.ticks_ms()
    # DHT11 needs at least 2 seconds between readings
    if time.ticks_diff(now, last_dht_ms) >= 2000:
        try:
            dht_s.measure()
            temp = dht_s.temperature()
            hum  = dht_s.humidity()
            last_dht_ms = now
        except Exception as e:
            pass   # keep last known values
    gas_adc_raw = gas_adc.read_u16()
    gas = min(int(gas_adc_raw * 10000 // 65535), 10000)
    flm = not flame_p.value()       # HW-072: LOW = flame
    mot = bool(pir_p.value())

def check_button():
    global prev_btn, prev_btn_ms
    b = btn_p.value()
    now = time.ticks_ms()
    if b == 0 and prev_btn == 1:
        if time.ticks_diff(now, prev_btn_ms) > DEBOUNCE:
            set_valve(not vlv_open)
            prev_btn_ms = now
    prev_btn = b

def safety_logic():
    global last_mot_ms, unattend_flag, last_alert_ms
    now = time.ticks_ms()
    alert = ""
    need_fan = False
    need_buz = False

    if mot:
        last_mot_ms = now
        unattend_flag = False

    # Rule 1 — gas high
    if gas > gas_thr:
        need_buz = True
        need_fan = True
        set_valve(False)
        if time.ticks_diff(now, last_alert_ms) > ALERT_COOL:
            alert = "GAS_HIGH"
            last_alert_ms = now

    # Rule 2 — flame detected
    if flm:
        set_valve(False)
        need_buz = True
        if not alert and time.ticks_diff(now, last_alert_ms) > ALERT_COOL:
            alert = "FLAME"
            last_alert_ms = now

    # Rule 3 — temp high
    if temp > temp_thr:
        need_fan = True

    # Rule 4 — unattended stove
    if temp > temp_thr and not mot:
        if time.ticks_diff(now, last_mot_ms) > UNATTEND_MS:
            unattend_flag = True
            set_valve(False)
            need_fan = False
            need_buz = False
            if not alert:
                alert = "UNATTENDED"

    if not unattend_flag:
        set_fan(need_fan)
        set_buz(need_buz)
    else:
        set_fan(False)
        set_buz(False)

    # ---- LED logic ----
    # Motion LED: solid ON when motion detected
    mot_led.value(1 if mot else 0)

    # Alert LED: blink when any alert condition is active
    in_alert = need_buz or flm or (gas > gas_thr)
    if in_alert:
        # Toggle LED every 250ms for blinking effect
        global alert_blink_ms
        if time.ticks_diff(now, alert_blink_ms) >= 250:
            alert_led.value(not alert_led.value())
            alert_blink_ms = now
    else:
        alert_led.value(0)

    return alert

def handle_cmds():
    global gas_thr, temp_thr
    if uart.any():
        try:
            line = uart.readline()
            if line:
                c = line.decode().strip()
                if c.startswith("SET_GAS_THRESH:"):
                    gas_thr = int(c.split(":")[1])
                elif c.startswith("SET_TEMP_THRESH:"):
                    temp_thr = int(c.split(":")[1])
                elif c == "CLOSE_VALVE":
                    set_valve(False)
                elif c == "OPEN_VALVE":
                    set_valve(True)
        except:
            pass

def send_data(al=""):
    d = json.dumps({
        "t": temp, "h": hum, "g": gas,
        "fl": 1 if flm else 0, "m": 1 if mot else 0,
        "fn": 1 if fan_on else 0, "bz": 1 if buz_on else 0,
        "sv": 1 if vlv_open else 0,
        "tm": cook_tmr, "gt": gas_thr, "tt": temp_thr,
        "al": al
    })
    uart.write(d + "\n")

#  MAIN 
# Boot-up servo test: sweep so user can verify hardware
print("Smart Kitchen System Starting...")
print("Testing servo...")
servo_angle(0)           # go to 0°
time.sleep_ms(500)
servo_angle(90)          # go to 90° (open)
time.sleep_ms(500)
servo_angle(0)           # back to 0° (closed)
time.sleep_ms(500)
servo_angle(90)          # final state: OPEN
print("Servo test complete.")

vlv_open = True          # valve starts OPEN
set_fan(False)
set_buz(False)
alert_led.value(0)
mot_led.value(0)
print("Smart Kitchen System Started")

while True:
    now = time.ticks_ms()
    check_button()

    if time.ticks_diff(now, last_read) >= INTERVAL:
        read_sensors()
        last_read = now

    al = safety_logic()
    if al:
        pending_alert = al   # store so it doesn't get lost

    handle_cmds()

    if time.ticks_diff(now, last_send) >= INTERVAL:
        send_data(pending_alert)
        pending_alert = ""   # clear after sending
        last_send = now

    time.sleep_ms(10)
