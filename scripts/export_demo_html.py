import os
import json
import numpy as np
import tensorflow as tf

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
MODEL_PATH = os.path.join(BASE_DIR, "models", "wrist_fall_model_quant.tflite")
HTML_TEMPLATE_PATH = os.path.join(BASE_DIR, "scripts", "prefall_dashboard.html")
OUTPUT_HTML_PATH = os.path.join(BASE_DIR, "presentation_dashboard.html")

# 1. Load Processed Dataset
X_wrist = np.load(os.path.join(DATA_DIR, "X_wrist_50hz.npy"))
y_labels = np.load(os.path.join(DATA_DIR, "y_labels_50hz.npy"))

fall_indices = np.where(y_labels == 1)[0][:25].tolist()
normal_indices = np.where(y_labels == 0)[0][:25].tolist()

# 2. Load Quantized TFLite Model
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def predict_sample(sample_window):
    in_detail = input_details[0]
    out_detail = output_details[0]
    quant_params = in_detail.get('quantization_parameters', {})
    scales = quant_params.get('scales', np.array([]))
    zero_points = quant_params.get('zero_points', np.array([]))

    sample_prep = np.expand_dims(sample_window, axis=0).astype(np.float32)
    if len(scales) > 0 and scales[0] > 0:
        scale, zp = scales[0], zero_points[0]
        input_data = np.clip(np.round(sample_prep / scale) + zp, -128, 127).astype(np.int8)
    else:
        input_data = sample_prep.astype(in_detail['dtype'])

    interpreter.set_tensor(in_detail['index'], input_data)
    interpreter.invoke()
    raw_output = interpreter.get_tensor(out_detail['index'])

    out_quant_params = out_detail.get('quantization_parameters', {})
    out_scales = out_quant_params.get('scales', np.array([]))
    out_zps = out_quant_params.get('zero_points', np.array([]))

    if len(out_scales) > 0 and out_scales[0] > 0:
        o_scale, o_zp = out_scales[0], out_zps[0]
        probs = (raw_output.astype(np.float32) - o_zp) * o_scale
    else:
        probs = raw_output.astype(np.float32)

    probs = np.clip(probs[0], 0.0, 1.0)
    prob_sum = np.sum(probs)
    if prob_sum > 0:
        probs /= prob_sum
    return float(probs[0]), float(probs[1])

# 3. Generate Evaluation Data Payload
payload = {"fall": {}, "adl": {}}

for idx in fall_indices:
    raw_win = X_wrist[idx]
    p_norm, p_fall = predict_sample(raw_win)
    total_acc = np.sqrt(raw_win[:, 0]**2 + raw_win[:, 1]**2 + raw_win[:, 2]**2)
    payload["fall"][str(idx)] = {
        "window": raw_win[:, :3].tolist(),  # [Ax, Ay, Az]
        "min_a": float(np.min(total_acc)),
        "max_a": float(np.max(total_acc)),
        "p_normal": p_norm,
        "p_fall": p_fall,
        "tier1": bool(np.min(total_acc) < 0.50)
    }

for idx in normal_indices:
    raw_win = X_wrist[idx]
    p_norm, p_fall = predict_sample(raw_win)
    total_acc = np.sqrt(raw_win[:, 0]**2 + raw_win[:, 1]**2 + raw_win[:, 2]**2)
    payload["adl"][str(idx)] = {
        "window": raw_win[:, :3].tolist(),
        "min_a": float(np.min(total_acc)),
        "max_a": float(np.max(total_acc)),
        "p_normal": p_norm,
        "p_fall": p_fall,
        "tier1": bool(np.min(total_acc) < 0.50)
    }

# 4. Inject Payload into the HTML Template
with open(HTML_TEMPLATE_PATH, "r", encoding="utf-8") as f:
    html_content = f.read()

injection_tag = f"<script>window.PREFALL_DATA = {json.dumps(payload)};</script>\n<script>"
html_content = html_content.replace("<script>", injection_tag, 1)

with open(OUTPUT_HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"\n[SUCCESS] Standalone dashboard generated at: {OUTPUT_HTML_PATH}")
print("Double-click presentation_dashboard.html to open it directly in your browser.")