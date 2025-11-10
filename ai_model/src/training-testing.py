import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

print("\nBuilding and training the LSTM model...")

model = Sequential([
    LSTM(8, input_shape=(X_train.shape[1], X_train.shape[2]), activation='tanh'),
    Dropout(0.2),
    Dense(1, activation='sigmoid')
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
model.summary()

history = model.fit(
    X_train, y_train,
    epochs=30,
    batch_size=32,
    validation_split=0.2,
    verbose=1
)

print("\nEvaluating model performance...")
loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
print(f"\nTest Accuracy: {accuracy*100:.2f}%")
print(f"Test Loss: {loss:.4f}")
y_pred_proba = model.predict(X_test)
y_pred = (y_pred_proba > 0.5).astype(int)
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=['Normal', 'Anomaly']))
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(6, 4))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Normal', 'Anomaly'], yticklabels=['Normal', 'Anomaly'])
plt.title('Confusion Matrix')
plt.ylabel('Actual Class')
plt.xlabel('Predicted Class')
plt.show()
print("\nStarting model conversion to TensorFlow Lite with quantization...")
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.target_spec.supported_ops = [
    tf.lite.OpsSet.TFLITE_BUILTINS,
    tf.lite.OpsSet.SELECT_TF_OPS
]
converter._experimental_lower_tensor_list_ops = False

converter.optimizations = [tf.lite.Optimize.DEFAULT]
def representative_dataset():
    for i in range(100):
        yield [X_train[i:i+1].astype(np.float32)]
converter.representative_dataset = representative_dataset


tflite_model_quant = converter.convert()
model_size_kb = len(tflite_model_quant) / 1024
print(f"\nConversion complete. Quantized model size: {model_size_kb:.2f} KB")
print("\nGenerating C++ header file: model_data.h")
def hex_to_c_array(hex_data, var_name):
    c_str = ''
    c_str += '#ifndef GUARDIAN_MODEL_DATA_H\n'
    c_str += '#define GUARDIAN_MODEL_DATA_H\n\n'
    c_str += f'// TensorFlow Lite model, quantized and converted for the Guardian project.\n'
    c_str += f'// Model size: {model_size_kb:.2f} KB\n\n'
    c_str += f'unsigned const char {var_name}[] = {{\n'
    hex_array = []
    for i, val in enumerate(hex_data):
        hex_str = format(val, '#04x')
        if (i + 1) % 12 == 0:
            hex_str += '\n'
        hex_array.append(hex_str)
    c_str += ', '.join(hex_array)
    c_str += '\n};\n\n'
    c_str += f'unsigned int {var_name}_len = {len(hex_data)};\n\n'
    c_str += '#endif // GUARDIAN_MODEL_DATA_H\n'
    return c_str

c_model_str = hex_to_c_array(tflite_model_quant, 'g_guardian_model_data')

with open('model_data.h', 'w') as f:
    f.write(c_model_str)

print("-" * 50)
print("COPY AND PASTE THE FOLLOWING CODE INTO A NEW FILE NAMED 'model_data.h' IN YOUR ARDUINO PROJECT:")
print("-" * 50)
print(c_model_str)
print("-" * 50)