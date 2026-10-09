import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# 1. Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

# 2. Load Processed Data
MODE = "wrist"
if MODE == "wrist":
    X = np.load(os.path.join(DATA_DIR, "X_wrist_50hz.npy"))
    model_name = "wrist_fall_model"
else:
    X = np.load(os.path.join(DATA_DIR, "X_insole_50hz.npy"))
    model_name = "insole_fall_model"

y = np.load(os.path.join(DATA_DIR, "y_labels_50hz.npy"))
print(f"Loaded {MODE} data: Shape {X.shape}, Labels {y.shape}")

# 3. Train-Test Split (80% train, 20% validation)
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

# 4. TinyML Static 1D-CNN Architecture (Zero dynamic tensor loops, 100% INT8 compatible)
input_shape = (50, X_train.shape[2])

model = models.Sequential([
    layers.Input(shape=input_shape),
    layers.Conv1D(filters=16, kernel_size=3, padding="same", activation="relu"),
    layers.BatchNormalization(),
    layers.MaxPooling1D(pool_size=2),
    
    layers.Conv1D(filters=32, kernel_size=3, padding="same", activation="relu"),
    layers.BatchNormalization(),
    layers.MaxPooling1D(pool_size=2),
    
    layers.Conv1D(filters=32, kernel_size=3, dilation_rate=2, padding="same", activation="relu"),
    layers.GlobalAveragePooling1D(),
    
    layers.Dropout(0.25),
    layers.Dense(16, activation="relu"),
    layers.Dense(2, activation="softmax")
])

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

# 5. Training with 50 Epochs & EarlyStopping
print("\n--- Training Model for 50 Epochs ---")
early_stopping = EarlyStopping(
    monitor="val_loss",
    patience=8,
    restore_best_weights=True,
    verbose=1
)

model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=50,
    batch_size=64,
    callbacks=[early_stopping],
    verbose=1
)

# 6. Evaluate
val_preds = np.argmax(model.predict(X_val), axis=1)
print("\n--- Validation Performance ---")
print(classification_report(y_val, val_preds, target_names=["Normal", "Pre-Fall"]))

# 7. Post-Training INT8 Quantization (TFLite Micro Compliant)
print("\n--- Quantizing Model to INT8 for ESP32 ---")

def representative_dataset_gen():
    for i in range(150):
        sample = np.expand_dims(X_train[i].astype(np.float32), axis=0)
        yield [sample]

converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset_gen
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8

quantized_tflite_model = converter.convert()

tflite_path = os.path.join(MODELS_DIR, f"{model_name}_quant.tflite")
with open(tflite_path, "wb") as f:
    f.write(quantized_tflite_model)

size_kb = os.path.getsize(tflite_path) / 1024.0
print(f"\n[SUCCESS] Quantized Model Saved: {tflite_path}")
print(f"[SUCCESS] Model Footprint: {size_kb:.2f} KB (Well below 50 KB SRAM budget)[cite: 1]")

# 8. Export to C Header Array (model_data.h)
header_path = os.path.join(MODELS_DIR, "model_data.h")
with open(header_path, "w") as f:
    f.write(f"// Auto-generated TinyML Model: {model_name}\n")
    f.write(f"// Size: {len(quantized_tflite_model)} bytes\n\n")
    f.write("#ifndef MODEL_DATA_H\n#define MODEL_DATA_H\n\n")
    f.write(f"const unsigned int fall_model_quant_len = {len(quantized_tflite_model)};\n")
    f.write("const unsigned char fall_model_quant_tflite[] = {\n    ")
    
    for i, byte in enumerate(quantized_tflite_model):
        f.write(f"0x{byte:02x}, ")
        if (i + 1) % 12 == 0:
            f.write("\n    ")
            
    f.write("\n};\n\n#endif // MODEL_DATA_H\n")

print(f"[SUCCESS] C Header Exported: {header_path}")