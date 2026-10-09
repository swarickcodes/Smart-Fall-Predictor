import os
import glob
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, resample

# --- PATH CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "raw", "sensor_data")
LABEL_DIR = os.path.join(BASE_DIR, "data", "raw", "label_data")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- SAMPLING CONSTANTS ---
ORIGINAL_HZ = 100
TARGET_HZ = 50
WINDOW_SIZE = 50   # 1 second at 50 Hz
STEP_SIZE = 25     # 50% overlap

def butter_lowpass_filter(data, cutoff=20.0, fs=50.0, order=2):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return filtfilt(b, a, data, axis=0)

def process_pipeline():
    X_wrist_list, X_insole_list, y_list = [], [], []
    
    subject_folders = sorted(glob.glob(os.path.join(DATA_DIR, "SA*")))
    if not subject_folders:
        print(f"[ERROR] No subject directories found in {DATA_DIR}")
        return

    for sub_path in subject_folders:
        sub_id = os.path.basename(sub_path)
        print(f"[INFO] Processing {sub_id}...")

        # Load labels file
        label_file_xlsx = os.path.join(LABEL_DIR, f"{sub_id}_label.xlsx")
        label_file_csv = os.path.join(LABEL_DIR, f"{sub_id}_label.csv")
        labels_df = None

        if os.path.exists(label_file_xlsx):
            labels_df = pd.read_excel(label_file_xlsx)
        elif os.path.exists(label_file_csv):
            labels_df = pd.read_csv(label_file_csv)

        csv_files = glob.glob(os.path.join(sub_path, "*.csv"))

        for file_path in csv_files:
            filename = os.path.basename(file_path)
            # Example filename: SA06T20R01.csv
            try:
                task_id = int(filename.split("T")[1].split("R")[0])
                trial_id = int(filename.split("R")[1].split(".")[0])
            except (IndexError, ValueError):
                continue

            is_fall_trial = (task_id > 21)

            df = pd.read_csv(file_path)
            # Columns: [0:TimeStamp, 1:FrameCounter, 2:Ax, 3:Ay, 4:Az, 5:Gx, 6:Gy, 7:Gz]
            raw_imu = df.iloc[:, 2:8].values.astype(np.float32)

            if len(raw_imu) < 100:
                continue

            # 1. Resample to 50 Hz
            target_samples = int(len(raw_imu) * (TARGET_HZ / ORIGINAL_HZ))
            resampled_imu = resample(raw_imu, target_samples)

            # 2. Filter
            filtered_imu = butter_lowpass_filter(resampled_imu, cutoff=20.0, fs=TARGET_HZ)

            # 3. Pre-Fall Phase Detection
            onset_50hz, impact_50hz = None, None
            if is_fall_trial and labels_df is not None:
                match = labels_df[(labels_df.iloc[:, 0] == task_id) & (labels_df.iloc[:, 2] == trial_id)]
                if not match.empty:
                    onset_50hz = int(match.iloc[0, 3] * (TARGET_HZ / ORIGINAL_HZ))
                    impact_50hz = int(match.iloc[0, 4] * (TARGET_HZ / ORIGINAL_HZ))

            # Fallback: estimate impact using >3g acceleration threshold
            if is_fall_trial and impact_50hz is None:
                acc_mag = np.linalg.norm(filtered_imu[:, 0:3], axis=1)
                spike_idx = np.where(acc_mag > 3.0)[0]
                if len(spike_idx) > 0:
                    impact_50hz = spike_idx[0]
                    onset_50hz = max(0, impact_50hz - 25)

            # 4. Generate Synthesized Ground Reaction Force (GRF) for Insole
            # Foot contact drops during trip/slip instability
            total_acc = np.linalg.norm(filtered_imu[:, 0:3], axis=1, keepdims=True)
            insole_grf = np.clip(total_acc / 1.0, 0.0, 2.0)
            insole_stream = np.hstack([filtered_imu, insole_grf]) # 7 channels: 6 IMU + 1 GRF

            # 5. Add Motion Artifacts for Wristband Data
            # Gaussian noise simulates limb swing
            noise = np.random.normal(0, 0.03, filtered_imu.shape)
            wrist_stream = filtered_imu + noise

            # 6. Slicing into Windows
            num_rows = len(filtered_imu)
            for start in range(0, num_rows - WINDOW_SIZE, STEP_SIZE):
                end = start + WINDOW_SIZE
                label = 0

                if is_fall_trial and impact_50hz is not None:
                    pre_fall_start = max(0, impact_50hz - 20) # 400 ms before impact
                    pre_fall_end = impact_50hz

                    # Label pre-fall if window intersects the instability phase
                    if (start <= pre_fall_end) and (end >= pre_fall_start):
                        label = 1
                    elif start > impact_50hz:
                        # Exclude post-impact flat-ground data
                        continue

                X_wrist_list.append(wrist_stream[start:end])
                X_insole_list.append(insole_stream[start:end])
                y_list.append(label)

    # Convert to Numpy Arrays
    X_wrist = np.array(X_wrist_list, dtype=np.float32)
    X_insole = np.array(X_insole_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)

    # Save to disk
    np.save(os.path.join(OUTPUT_DIR, "X_wrist_50hz.npy"), X_wrist)
    np.save(os.path.join(OUTPUT_DIR, "X_insole_50hz.npy"), X_insole)
    np.save(os.path.join(OUTPUT_DIR, "y_labels_50hz.npy"), y)

    print("\n--- Summary ---")
    print(f"Wrist dataset shape:  {X_wrist.shape}  (Windows, 50 samples, 6 channels)")
    print(f"Insole dataset shape: {X_insole.shape} (Windows, 50 samples, 7 channels)")
    print(f"Class Distribution:   Normal (0): {np.sum(y == 0)} | Pre-Fall (1): {np.sum(y == 1)}")

if __name__ == "__main__":
    process_pipeline()