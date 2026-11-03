#include <Wire.h>
#include <EloquentTinyML.h>
#include "model_data.h"

// --- HARDWARE PIN ASSIGNMENTS ---
#define PIN_FSR_HEEL   34  // Plantar Calcaneus (ADC1_CH6)
#define PIN_FSR_INNER  35  // Plantar 1st Metatarsal (ADC1_CH7)
#define PIN_FSR_OUTER  32  // Plantar 5th Metatarsal (ADC1_CH4)
#define PIN_BUZZER     25  // Active Buzzer Drive Pin
#define I2C_SDA_PIN    21  // MPU-6050 SDA
#define I2C_SCL_PIN    22  // MPU-6050 SCL

#define MPU_ADDR       0x68

// --- TINYML CONFIGURATION ---
#define NUMBER_OF_INPUTS   300 
#define NUMBER_OF_OUTPUTS  1   // Raw linear logit output
#define TENSOR_ARENA_SIZE  (20 * 1024)

Eloquent::TinyML::TfLite<NUMBER_OF_INPUTS, NUMBER_OF_OUTPUTS, TENSOR_ARENA_SIZE> ml;

// Time-series ring buffer
#define MODEL_TIMESTEPS 50
#define MODEL_CHANNELS  6
float ring_buffer[MODEL_TIMESTEPS][MODEL_CHANNELS];
int ring_head = 0;
bool buffer_primed = false;

// Flattened input tensor buffer
float model_input[NUMBER_OF_INPUTS];

// Sampling loop (25 Hz = 40 ms interval)
constexpr unsigned long SAMPLE_INTERVAL_MS = 40;
unsigned long last_sample_time = 0;

// Buzzer Alarm timing
bool alarm_active = false;
unsigned long alarm_start_time = 0;
constexpr unsigned long ALARM_DURATION_MS = 1500;

// Conversion factors
const float ACCEL_SCALE = (4.0f * 9.80665f) / 32768.0f; // +/- 4g scale
const float FSR_SCALE   = 1.0f / 4095.0f;               // 12-bit ADC normalizer

// --- KFALL BASELINE PRE-LOAD VALUES (ADL NORMAL STANCE) ---
// [Ax, Ay, Az, Heel, Inner, Outer]
const float KFALL_BASELINE_AX    = 0.12f;
const float KFALL_BASELINE_AY    = 0.15f;
const float KFALL_BASELINE_AZ    = 9.78f;  // Earth gravity component (1g)
const float KFALL_BASELINE_HEEL  = 0.48f;  // Calcaneus weight distribution
const float KFALL_BASELINE_INNER = 0.35f;  // 1st Metatarsal distribution
const float KFALL_BASELINE_OUTER = 0.32f;  // 5th Metatarsal distribution

void recoverI2CBus() {
  pinMode(I2C_SDA_PIN, INPUT_PULLUP);
  pinMode(I2C_SCL_PIN, OUTPUT);

  for (int i = 0; i < 9; i++) {
    digitalWrite(I2C_SCL_PIN, HIGH);
    delayMicroseconds(5);
    digitalWrite(I2C_SCL_PIN, LOW);
    delayMicroseconds(5);
  }

  pinMode(I2C_SDA_PIN, OUTPUT);
  digitalWrite(I2C_SDA_PIN, LOW);
  delayMicroseconds(5);
  digitalWrite(I2C_SCL_PIN, HIGH);
  delayMicroseconds(5);
  digitalWrite(I2C_SDA_PIN, HIGH);
  delayMicroseconds(5);
}

bool setupMPU() {
  recoverI2CBus();
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  Wire.setClock(100000);

  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);
  Wire.write(0x00);
  if (Wire.endTransmission(true) != 0) return false;
  delay(15);

  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x1C);
  Wire.write(0x08); // +/- 4g range
  if (Wire.endTransmission(true) != 0) return false;

  return true;
}

bool readSensors(float &ax, float &ay, float &az, float &heel, float &inner, float &outer) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return false;

  if (Wire.requestFrom((uint8_t)MPU_ADDR, (uint8_t)6, (uint8_t)true) == 6) {
    int16_t raw_ax = (Wire.read() << 8) | Wire.read();
    int16_t raw_ay = (Wire.read() << 8) | Wire.read();
    int16_t raw_az = (Wire.read() << 8) | Wire.read();

    ax = (float)raw_ax * ACCEL_SCALE;
    ay = (float)raw_ay * ACCEL_SCALE;
    az = (float)raw_az * ACCEL_SCALE;
  } else {
    return false;
  }

  heel  = (float)analogRead(PIN_FSR_HEEL)  * FSR_SCALE;
  inner = (float)analogRead(PIN_FSR_INNER) * FSR_SCALE;
  outer = (float)analogRead(PIN_FSR_OUTER) * FSR_SCALE;

  return true;
}

// Pre-fill rolling buffer with KFall standing baseline
void initializeBufferWithKFallBaseline() {
  for (int t = 0; t < MODEL_TIMESTEPS; t++) {
    ring_buffer[t][0] = KFALL_BASELINE_AX;
    ring_buffer[t][1] = KFALL_BASELINE_AY;
    ring_buffer[t][2] = KFALL_BASELINE_AZ;
    ring_buffer[t][3] = KFALL_BASELINE_HEEL;
    ring_buffer[t][4] = KFALL_BASELINE_INNER;
    ring_buffer[t][5] = KFALL_BASELINE_OUTER;
  }
  ring_head = 0;
  buffer_primed = true;
}

void triggerAlarm() {
  alarm_active = true;
  alarm_start_time = millis();
  digitalWrite(PIN_BUZZER, HIGH);
}

void updateAlarm() {
  if (alarm_active && (millis() - alarm_start_time >= ALARM_DURATION_MS)) {
    digitalWrite(PIN_BUZZER, LOW);
    alarm_active = false;
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000);

  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_BUZZER, LOW);

  pinMode(PIN_FSR_HEEL, INPUT);
  pinMode(PIN_FSR_INNER, INPUT);
  pinMode(PIN_FSR_OUTER, INPUT);

  analogSetPinAttenuation(PIN_FSR_HEEL, ADC_11db);
  analogSetPinAttenuation(PIN_FSR_INNER, ADC_11db);
  analogSetPinAttenuation(PIN_FSR_OUTER, ADC_11db);

  Serial.println("\n=============================================");
  Serial.println("   Smart Insole Pre-Fall Prediction Engine   ");
  Serial.printf("   Quantized Model Size: %d bytes\n", fall_model_quant_len);
  Serial.println("=============================================");

  if (!setupMPU()) {
    Serial.println("[-] Error: MPU-6050 not detected at 0x68. Verify SDA/SCL lines.");
    while (1) {
      digitalWrite(PIN_BUZZER, HIGH); delay(80);
      digitalWrite(PIN_BUZZER, LOW);  delay(250);
    }
  }

  if (!ml.begin(fall_model_quant_tflite)) {
    Serial.println("[-] Error: Failed to initialize TensorFlow Lite Model!");
    while (1) delay(1000);
  }

  // Pre-seed buffer with normal KFall baseline stance
  initializeBufferWithKFallBaseline();

  Serial.println("[+] TensorFlow Lite Micro Initialized successfully.");
  Serial.println("[+] Pre-seeded with KFall standing baseline.");
  Serial.println("[+] Ready for live inference...\n");
}

void loop() {
  unsigned long now = millis();

  if (now - last_sample_time >= SAMPLE_INTERVAL_MS) {
    last_sample_time = now;

    float ax, ay, az, heel, inner, outer;
    if (readSensors(ax, ay, az, heel, inner, outer)) {
      ring_buffer[ring_head][0] = ax;
      ring_buffer[ring_head][1] = ay;
      ring_buffer[ring_head][2] = az;
      ring_buffer[ring_head][3] = heel;
      ring_buffer[ring_head][4] = inner;
      ring_buffer[ring_head][5] = outer;

      ring_head = (ring_head + 1) % MODEL_TIMESTEPS;

      // Flatten the 50x6 circular buffer into the 300-float input vector
      int idx = 0;
      for (int t = 0; t < MODEL_TIMESTEPS; t++) {
        int ring_t = (ring_head + t) % MODEL_TIMESTEPS;
        for (int c = 0; c < MODEL_CHANNELS; c++) {
          model_input[idx++] = ring_buffer[ring_t][c];
        }
      }

      // --- INFERENCE FORWARD PASS ---
      float model_output[NUMBER_OF_OUTPUTS] = {0.0f};
      ml.predict(model_input, model_output);

      // Hardware-native C++ Sigmoid conversion
      float logit = model_output[0];
      float pre_fall_prob = 1.0f / (1.0f + exp(-logit));
      pre_fall_prob = constrain(pre_fall_prob, 0.0f, 1.0f);

      // Unloaded desk safeguard:
      // If the insole is on a table with zero pressure applied, hold at baseline
      float current_pressure = heel + inner + outer;
      if (current_pressure < 0.05f) {
        pre_fall_prob = 0.02f; // Idle / Unworn State
      }

      Serial.printf("Ax:%5.1f | Heel:%4d | Outer:%4d | Inner:%4d | NN_Prob:%.2f",
                    ax, (int)(heel * 4095), (int)(outer * 4095), (int)(inner * 4095), pre_fall_prob);

      if (pre_fall_prob >= 0.70f) {
        Serial.println(" -> [!] PRE-FALL DETECTED!");
        triggerAlarm();
      } else {
        Serial.println(" -> Normal Gait / Idle");
      }
    }
  }

  updateAlarm();
}