# -*- coding: utf-8 -*-
"""Rough Implementation

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1nokRqNSE5GZcXXdT83ESXqec2RgXDCiV

Download database.
"""

!wget -r -N -c -np -q https://physionet.org/files/slpdb/1.0.0/

"""Download libraries."""

!pip install -q wfdb
!python -m pip uninstall -q matplotlib
!pip install -q matplotlib==3.1.3

"""Import libraries."""

# For reading database
import wfdb
import os
import copy
import numpy as np
import scipy as sp
from tensorflow.keras import models, layers
from tensorflow.keras import utils
import matplotlib.pyplot as plt
import librosa
import librosa.display

np.random.seed(1)

"""## **1. Import Database**
Accessing data and basic data processing.

"""

class PatientData (object):
    ECG_signal = None
    EEG_signal = None
    sleep_stages = None

    record_length = None
    sampling_frequency = None

    def __init__ (self, patient_name):
        self.patient_name = patient_name

DATABASE_PATH = 'physionet.org/files/slpdb/1.0.0'

with open(os.path.join(DATABASE_PATH, 'RECORDS'), 'r') as file:
    PATIENT_NAMES = file.read().split('\n')[:-1]
  
PATIENTS = {
    patient_name: PatientData(patient_name)
    for patient_name in PATIENT_NAMES
}

# 0 Awake
# 1 NREM stage 1
# 2 NREM stage 2
# 3 NREM stage 3 and 4
# 4 REM
def annotation_sleep_stage (annotation):
    if annotation.startswith('W'):
        return 0
    elif annotation.startswith('1'):
        return 1
    elif annotation.startswith('2'):
        return 2
    elif annotation.startswith('3') or annotation.startswith('4'):
        return 3
    elif annotation.startswith('R'):
        return 4
    # Ideally, all annotations are classified into one of the above 5
    else:
        return -1

# Since annotations only have labels and the time at which they occur,
# interpolate all the data so there's always a label at each time step
def step_interpolation (data, locations, total_length):
    step_interpolated_data = np.zeros(total_length)

    for i in range(len(locations) - 1):
        start_range = locations[i]
        end_range = locations[i + 1]

        # Convert string annotation into sleep stage
        step_interpolated_data[(start_range - 1) : end_range] = annotation_sleep_stage(data[i])

    return step_interpolated_data

for patient_name in PATIENT_NAMES:
    patient = PATIENTS[patient_name]

    # Retrieve raw signals and annotations
    record_path = os.path.join(DATABASE_PATH, patient_name)
    record = wfdb.io.rdrecord(record_path)
    annotation = wfdb.rdann(record_path, extension='st')

    # Sampling frequency
    # This might differ for each record
    patient.sampling_frequency = record.fs

    # 0 ECG
    # 1 BP
    # 2 EEG
    # 3 Resp (not available for all)
    patient.ECG_signal = record.p_signal[:, 0]
    patient.EEG_signal = record.p_signal[:, 2]
    patient.record_length = record.sig_len

    patient.sleep_stages = step_interpolation(annotation.aux_note, annotation.sample, patient.record_length)

# Example patient
patient_slp01a = PATIENTS['slp01a']
print(patient_slp01a.ECG_signal)
print(patient_slp01a.EEG_signal)
print(patient_slp01a.sleep_stages)

# Splitting the dataset into train, validation, test set
# Will be split in terms of patients, not sleep data
num_patients = len(PATIENTS)

# Shuffle patients
randomized_patients = copy.deepcopy(list(PATIENTS.keys()))
np.random.shuffle(randomized_patients)

# 80 / 10 / 10 split of 18 patients will be roughly 14 / 2 / 2
# Don't need test_end, since it'll be until the end of data
train_end = 14
valid_end = train_end + 2

# Split data using keys
train_patients = randomized_patients[ : train_end]
valid_patients = randomized_patients[train_end : valid_end]
test_patients = randomized_patients[valid_end : ]

"""## **2. Building the Neural Network**"""

# Sample data to test out CNN
sample_patient = PATIENTS[train_patients[0]]

# One batch is 30 seconds of EEG and ECG data
num_samples_in_one_second = float(1 / sample_patient.sampling_frequency)
num_samples_in_one_datum = int(30 / num_samples_in_one_second)

# Calculate MFCC's for both EEG and ECG
sample_EEG_MFCC = librosa.feature.melspectrogram(
    y=sample_patient.EEG_signal[ : num_samples_in_one_datum], 
    sr=sample_patient.sampling_frequency)
sample_ECG_MFCC = librosa.feature.melspectrogram(
    y=sample_patient.ECG_signal[ : num_samples_in_one_datum], 
    sr=sample_patient.sampling_frequency)

sample_EEG_MFCC_db = librosa.power_to_db(sample_EEG_MFCC)
librosa.display.specshow(
    sample_EEG_MFCC_db, 
    x_axis='time', 
    y_axis='mel', 
    sr=sample_patient.sampling_frequency)

train_data = None
train_labels = None

for patient_name in train_patients:
    # Get training data for one patient
    print("Batching {} patient data...".format(patient_name))
    patient = PATIENTS[patient_name]

    # Calculate total number of samples for this patient
    total_num_samples = int(patient.EEG_signal.shape[0] / num_samples_in_one_datum)

    for i in range(total_num_samples):
        # Determine start and end of current batch
        start = (i * num_samples_in_one_datum)
        end = ((i + 1) * num_samples_in_one_datum)
        
        EEG_MFCC = librosa.feature.melspectrogram(
            y=patient.EEG_signal[start : end], 
            sr=patient.sampling_frequency)
        ECG_MFCC = librosa.feature.melspectrogram(
            y=patient.ECG_signal[start : end], 
            sr=patient.sampling_frequency)
        
        sample = np.expand_dims(
            np.stack([ EEG_MFCC, ECG_MFCC ], axis=2), 
            axis=0)
        
        # Only grab the label at the end of the current batch
        # This is such that we're using all of the data in the current batch
        # in order to predict the sleep stage by the end of the batch
        sample_labels = np.array([ patient.sleep_stages[end - 1] ])

        if train_data is None:
            train_data = sample
            train_labels = sample_labels
        else:
            train_data = np.append(train_data, sample, axis=0)
            train_labels = np.append(train_labels, sample_labels, axis=0)

    break

print(train_data.shape)
print(train_labels.shape)

filter_size = 3
pool_size = 2

width, height = sample_EEG_MFCC.shape

model = models.Sequential([
    layers.Conv2D(16, (filter_size, filter_size), activation='relu', input_shape=(width, height, 2)),
    layers.MaxPooling2D((pool_size, pool_size)),

    layers.Flatten(), 
    layers.Dense(32, activation='relu'),
    layers.Dense(5, activation='softmax')
])

# Compile the model
model.compile(
    optimizer = 'adam',
    loss='categorical_crossentropy',
    metrics=['accuracy'],
)

model.summary()

# Train the neural network

history = model.fit(
  train_data,
  utils.to_categorical(train_labels),
  epochs=10
)

# Graph training accuracy
plt.plot(history.history['accuracy'], label='accuracy')
plt.xlabel('epoch')
plt.ylabel('accuracy')
plt.ylim([0, 1])
plt.legend(loc='lower right')

# Get accuracy of the network
model.evaluate(validation_data)

# implementing the class of conv net -- incompleted
class CNN_sleep_stages(tf.Module):
  def __init__(self, number_of_channels = , number_of_classes =):
    self.conv1 = models.Sequential(layers.Conv2D(, (, ), activation='relu', input_shape=(, , )))
    self.conv2 = models.Sequential(layers.Conv2D(, (, ), activation='relu'))
    self.pool =  models.Sequential(layers.MaxPool2D( 2 , 2 ))
    self.flat = models.Sequential(layers.Flatten())
    self.dense = models.Sequential(layers.Dense(, activation = 'Sigmoid'))
  
  def __call__(self, x):
    x = self.pool(self.conv1(x))
    return x

# Could improve the accuracy by:
# 1. Increasing the depth (adding more convolutional layer)
# 2. Adding dropout layer
# 3. Add fully-connected layers
# 4. Strides? Padding?