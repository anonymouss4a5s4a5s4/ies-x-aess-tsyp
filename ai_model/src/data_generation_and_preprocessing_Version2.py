
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt

def generate_guardian_data(n_samples_normal=3000, n_samples_anomaly=500):

    time_normal = np.arange(n_samples_normal)
    temp_normal = 20 * np.sin(time_normal / 150) + 25
    volt_normal = 0.4 * np.sin(time_normal / 50) + 3.8

    temp_normal += np.random.normal(0, 0.5, n_samples_normal)
    volt_normal += np.random.normal(0, 0.02, n_samples_normal)

    labels_normal = np.zeros(n_samples_normal)


    time_anomaly = np.arange(n_samples_anomaly)

    temp_anomaly_start = temp_normal[-1]
    temp_anomaly = temp_anomaly_start + (time_anomaly / 20)**2

    volt_anomaly_start = volt_normal[-1]
    volt_anomaly = volt_anomaly_start - (time_anomaly / 250)**1.5

    labels_anomaly = np.ones(n_samples_anomaly)

    temperatures = np.concatenate([temp_normal, temp_anomaly])
    voltages = np.concatenate([volt_normal, volt_anomaly])
    labels = np.concatenate([labels_normal, labels_anomaly])

    df = pd.DataFrame({
        'temperature': temperatures,
        'voltage': voltages,
        'label': labels
    })

    print("Data generation complete.")
    return df


df = generate_guardian_data()
df.to_csv('cubesat_sensor_data.csv', index=False)
fig, ax1 = plt.subplots(figsize=(15, 6))

ax1.set_xlabel('Time (samples)')
ax1.set_ylabel('Temperature (C)', color='red')
ax1.plot(df.index, df['temperature'], color='red', label='Temperature')
ax1.tick_params(axis='y', labelcolor='red')
ax1.axvline(x=3000, color='purple', linestyle='--', label='Anomaly Start')

ax2 = ax1.twinx()
ax2.set_ylabel('Voltage (V)', color='blue')
ax2.plot(df.index, df['voltage'], color='blue', label='Voltage')
ax2.tick_params(axis='y', labelcolor='blue')

plt.title('Synthetic CubeSat Sensor Data (Normal vs. Anomaly)')
plt.legend()
plt.show()

scaler = MinMaxScaler()
feature_data = df[['temperature', 'voltage']].values
scaled_features = scaler.fit_transform(feature_data)

labels = df['label'].values
SEQUENCE_LENGTH = 30

def create_sequences(features, labels, sequence_length):
    X, y = [], []
    for i in range(len(features) - sequence_length):
        X.append(features[i:(i + sequence_length)])
        y.append(labels[i + sequence_length])
    return np.array(X), np.array(y)

X, y = create_sequences(scaled_features, labels, SEQUENCE_LENGTH)

print(f"Created {len(X)} sequences of length {SEQUENCE_LENGTH}.")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Training data shape: {X_train.shape}")
print(f"Testing data shape: {X_test.shape}")