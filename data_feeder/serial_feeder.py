import numpy as np
import tensorflow as tf
from tensorflow.keras import models

import serial
import csv
import pickle
import time
from tabulate import tabulate

# Pickled test data
test_data = pickle.load(open("test_data.pkl", "rb"))
test_labels = pickle.load(open("test_labels.pkl", "rb"))
model = models.load_model('../model')

# CSV file
csv_file = open('classifications.csv', 'w', encoding='UTF8', newline='')
writer = csv.writer(csv_file)

print("Waiting to open serial communication...")

ser = serial.Serial(
    port='/dev/cu.usbmodem144101', 
    baudrate=38400,
    # 5 minutes
    timeout=300
)

print("Opened serial communication.")

start_at = 25
send_index = start_at
read_index = start_at
N = len(test_data)

COLORS = {
    0: "⚪️", 
    1: "🔵", 
    2: "🟢", 
    3: "🟣", 
    4: "🔴", 
    5: "⚫️"
}

SLEEP_STAGES = {
    0: "awake",
    1: "NREM 1",
    2: "NREM 2",
    3: "NREM 3",
    4: "REM",
    5: "unknown"
}

while read_index < N:
    # Found an input, print it
    while ser.in_waiting:
        response = int(ser.readline().decode())
        true_label = test_labels[read_index]
        print("({:<3}/{:<3}) {} Predicted: {} {:<7} \tActual: {}".format(
            read_index, N,
            "❌" if response != true_label else "✅",
            COLORS[response],
            SLEEP_STAGES[response],
            SLEEP_STAGES[int(true_label[0])]
        ))
        writer.writerow([str(response)]) 
        csv_file.flush()

        read_index += 1

    # Feed data to Arduino
    if send_index < N:
        probabilities = model.predict([test_data[send_index]])
        prediction = np.argmax(probabilities)
        ser.write((str(prediction)).encode())

        time.sleep(1.5)
        send_index += 1

print("Demo complete!")