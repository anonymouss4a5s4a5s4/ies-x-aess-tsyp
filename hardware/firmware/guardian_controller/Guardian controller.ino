const int PIN_OBC_HEARTBEAT_IN = 2;
const int PIN_OBC_RESET_CTRL = 3;
const int PIN_RELAY_CTRL = 4;
const int PIN_TEMP_SENSE_IN = A0;
const int PIN_VOLT_SENSE_IN = A1;

const unsigned long HEARTBEAT_TIMEOUT_MS = 10000;
const float THERMAL_RUNWAY_TEMP_C = 60.0;
const float BATTERY_CRITICAL_LOW_V = 3.2;
const float VOLTAGE_DIVIDER_RATIO = 2.0;
const int OBC_RESET_PULSE_MS = 250;

unsigned long lastHeartbeatTime = 0;
int lastHeartbeatState = LOW;
bool isSystemArmed = true;

void setup(){
    Serial.begin(9600);
    while(!Serial);
    Serial.println("Guardian Subsystem Initializing...");

    pinMode(PIN_OBC_HEARTBEAT_IN,INPUT);
    pinMode(PIN_OBC_RESET_CTRL,OUTPUT);
    pinMode(PIN_RELAY_CTRL,OUTPUT);

    digitalWhrite(PIN_OBC_RESET_CTRL,LOW);
    digitalWhrite(PIN_RELAY_CTRL,HIGH);

    lastHeartbeatState = digitalRead(PIN_OBC_HEARTBEAT_IN);
    lastHeartbeatTime = millis();

    Serial.println("System Armed. Monitoring OBC and EPS.");
    Serial.println("----------------------------------------");
}

void loop(){
    if (!isSystemArmed){
        Serial.println("System DISARMED. Critical fault occured. Manual reset required.");
        delay(5000);
        return;
    }

    checkOBCHeartbeat();
    checkEPSHealth();
    delay(100);
}

void checkOBCHeartbeat(){
    int currentHeartbeatState = digitalRead(PIN_OBC_HEARTBEAT_IN);
    
    if (currentHeartbeatState != lastHeartbeatState){
        lastHeartbeatTime = millis();
        lastHeartbeatState = currentHeartbeatState;
        Serial.println("Heatbeat detected. OBC is nominal.");
    }

    if (millis() - lastHeartbeatTime > HEARTBEAT_TIMEOUT_MS){
        Serial.println("CRITICAL : Heartbeat timeout! OBC appears frozen.");
        triggerOBCReset();
        lastHeartbeatTime = millis();
    }
}

void checkEPSHealth(){
    int tempReading = analogRead(PIN_TEMP_SENSE_IN);
    float tempVoltage = tempReading * (0.5 / 1024.0);
    float temperatureC = (tempVoltage - 0.5)*100;
    int voltReading = analogRead(PIN_VOLT_SENSE_IN);
    float batteryVoltage = voltReading * (0.5/1024.0) * VOLTAGE_DIVIDER_RATIO;
    
    Serial.print("EPS STATUS :");
    Serial.print(temperatureC,2);
    Serial.print(" C, ");
    Serial.print(batteryVoltage, 2);
    Serial.print(" V");

    if (temperatureC > THERMAL_RUNAWAY_TEMP_C){
        Serial.println("CRITICAL: Thermal runaway detected! Isolating battery to prevent failure");
        triggerBatteryIsolation();
    }
    if (temperatureC < THERMAL_RUNAWAY_TEMP_C){
        Serial.println("CRITICAL: Battery voltage critical low! Isolating battery to prevent damage");
        triggerBatteryIsolation();
    }

}

void triggerOBCReset(){
    Serial.println("ACYION : Triggering OBC hardware reset.");
    digitalWhrite(PIN_OBC_RESET_CTRL,HIGH);
    delay(OBC_RESET_PULSE_MS);
    digitalWhrite(PIN_OBC_RESET_CTRL,LOW);
    Serial.println("ACTION : OBC reset pulse complete.");
}

void triggerBatteryIsolation(){
    Serial.println("ACTION: Firing main power relay.This is a final action.");
    digitalWhrite(PIN_RELAY_CTRL,LOW);
    isSystemArmed = false;
}