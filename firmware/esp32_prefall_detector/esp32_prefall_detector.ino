#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <EloquentTinyML.h>
#include "model_data.h"

// --- 1. PIN DEFINITIONS ---
#define PIN_HAPTIC    6     // Drives 2N2222 transistor base for vibration motor
#define PIN_BUZZER    7     // Active piezo buzzer pin
#define I2C_SDA_PIN   8     // ESP32-S3 default I2C SDA
#define I2C_SCL_PIN   9     // ESP32-S3 default I2C SCL

// --- 2. TIMING CONSTANTS ---
#define SAMPLE_FREQ_HZ       50                      // 50 readings per second (matches ML training)
#define SAMPLE_INTERVAL_MS   (1000 / SAMPLE_FREQ_HZ) // Exactly 20 ms per loop tick
#define WINDOW_SIZE          50                      // 1.0 second sliding window (50 samples)
#define STEP_SIZE            25                      // 50% overlap hop (0.5 second)

// --- 3. TINYML ENGINE CONFIGURATION ---
#define NUMBER_OF_INPUTS     (50 * 6)                // 50 timesteps * 6 IMU axes = 300 inputs
#define NUMBER_OF_OUTPUTS    2                       // Class 0: Normal, Class 1: Pre-Fall
#define TENSOR_ARENA_SIZE    (25 * 1024)             // 25 KB internal RAM allocated for ML math

// Allocate TinyML runtime object
Eloquent::TinyML::TfLite<NUMBER_OF_INPUTS, NUMBER_OF_OUTPUTS, TENSOR_ARENA_SIZE> ml;

Adafruit_MPU6050 mpu;

// Rolling sensor buffer: 50 rows, 6 columns [Ax, Ay, Az, Gx, Gy, Gz]
float sensor_window[WINDOW_SIZE][6];
int sample_counter = 0;
unsigned long previous_sample_time = 0;

// Flat 1D array fed directly into the model input tensor
float ml_input_features[NUMBER_OF_INPUTS];

// --- 4. ALERT FUNCTION ---
void activate_alert() {
    Serial.println("[ALERT] >>> PRE-FALL DETECTED! TRIGGERING ACTUATORS <<<");
    digitalWrite(PIN_HAPTIC, HIGH); // Immediate tactile pulse (<10 ms response)
    digitalWrite(PIN_BUZZER, HIGH); // Immediate acoustic chime
    delay(250);                     // Buzz for 250 ms
    digitalWrite(PIN_HAPTIC, LOW);
    digitalWrite(PIN_BUZZER, LOW);
}

// --- 5. INITIALIZATION SETUP ---
void setup() {
    Serial.begin(115200);
    while (!Serial && millis() < 3000); // Allow USB serial to link up

    Serial.println("\n--- Initializing ESP32-S3 Pre-Fall Detector ---");

    // Configure Actuators
    pinMode(PIN_HAPTIC, OUTPUT);
    pinMode(PIN_BUZZER, OUTPUT);
    digitalWrite(PIN_HAPTIC, LOW);
    digitalWrite(PIN_BUZZER, LOW);

    // Initialize I2C communication on GPIO 8 and 9
    Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
    Wire.setClock(400000); // 400 kHz Fast-Mode I2C

    // Initialize MPU-6050 IMU
    if (!mpu.begin()) {
        Serial.println("[ERROR] MPU-6050 not found! Check 3V3, GND, SDA, and SCL wiring.");
        while (1) { delay(100); }
    }
    Serial.println("[OK] MPU-6050 initialized.");

    // Set Sensor Ranges matching our training conditions
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);   // ±8g range (impact headroom)
    mpu.setGyroRange(MPU6050_RANGE_500_DEG);        // ±500 °/s range
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);     // Onboard low-pass filter at ~21 Hz

    // Initialize the TinyML Inference Engine with model_data.h array
    if (!ml.begin(fall_model_quant_tflite)) {
        Serial.println("[ERROR] Failed to start TinyML engine. Check tensor arena size.");
        while (1) { delay(100); }
    }
    Serial.println("[OK] TinyML INT8 Engine loaded successfully.");
    Serial.println("[READY] System active. Sampling at 50 Hz...\n");
}

// --- 6. REAL-TIME LOOP ---
void loop() {
    unsigned long current_time = millis();

    // Enforce exact 20 ms timer intervals (50 Hz)
    if (current_time - previous_sample_time >= SAMPLE_INTERVAL_MS) {
        previous_sample_time = current_time;

        // Poll sensor
        sensors_event_t a, g, temp;
        mpu.getEvent(&a, &g, &temp);

        // Record 6 axes into sliding buffer
        sensor_window[sample_counter][0] = a.acceleration.x;
        sensor_window[sample_counter][1] = a.acceleration.y;
        sensor_window[sample_counter][2] = a.acceleration.z;
        sensor_window[sample_counter][3] = g.gyro.x;
        sensor_window[sample_counter][4] = g.gyro.y;
        sensor_window[sample_counter][5] = g.gyro.z;

        // --- TIER 1: FAST HEURISTIC THRESHOLD (Wu 2000 Baseline) ---
        // During early loss of balance or free-fall drop, resultant acceleration collapses < 0.5g (< 4.9 m/s^2)
        float total_acc = sqrt(sq(a.acceleration.x) + sq(a.acceleration.y) + sq(a.acceleration.z));
        if (total_acc < 4.90f) {
            Serial.print("[TIER 1 TRIGGER] Free-fall detected! Acceleration: ");
            Serial.print(total_acc);
            Serial.println(" m/s^2");
            activate_alert();
            sample_counter = 0; // Reset buffer
            return;
        }

        sample_counter++;

        // --- TIER 2: TINYML 1D-CNN INFERENCE ---
        // Once 50 samples (1.0 second of motion) are gathered, run the neural network
        if (sample_counter >= WINDOW_SIZE) {
            unsigned long start_micros = micros();

            // Flatten 2D window (50x6) into 1D array of 300 values
            int flat_idx = 0;
            for (int i = 0; i < WINDOW_SIZE; i++) {
                for (int c = 0; c < 6; c++) {
                    ml_input_features[flat_idx++] = sensor_window[i][c];
                }
            }

            // Execute neural network on the ESP32-S3
            float output[2] = {0.0f, 0.0f};
            ml.predict(ml_input_features, output);

            unsigned long duration_us = micros() - start_micros;
            float pre_fall_confidence = output[1]; // Index 1 is Class 1 (Pre-Fall)

            // Print telemetry
            Serial.print("[INFERENCE] Time: ");
            Serial.print(duration_us / 1000.0);
            Serial.print(" ms | Normal: ");
            Serial.print(output[0] * 100.0, 1);
            Serial.print("% | Pre-Fall: ");
            Serial.print(pre_fall_confidence * 100.0, 1);
            Serial.println("%");

            // If model is >= 75% confident this is a pre-fall stumble, trigger alert
            if (pre_fall_confidence >= 0.75f) {
                activate_alert();
            }

            // 50% Overlap Shift: move the newest 25 samples to the start of the buffer
            for (int i = 0; i < STEP_SIZE; i++) {
                for (int c = 0; c < 6; c++) {
                    sensor_window[i][c] = sensor_window[i + STEP_SIZE][c];
                }
            }
            sample_counter = STEP_SIZE; // Ready to collect 25 more samples for next hop
        }
    }
}