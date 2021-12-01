'''
    IMPORTS
'''
import os
import copy
import numpy as np

# For neural networks
from tensorflow.keras import models, layers
from tensorflow.keras import utils
import matplotlib.pyplot as plt

# For extracting MFCC's from ECG
import librosa
import librosa.display

# Custom libraries for organization
import data_processor as dp
import models as m



'''
    INITIAL SET-UP
'''
np.random.seed(1)

PATIENTS = dp.get_patients()

# Example patient
patient_slp01a = PATIENTS['slp01a']
print(patient_slp01a.ECG_signal)
print(patient_slp01a.EEG_signal)
print(patient_slp01a.sleep_stages)

# Splitting the dataset into train, validation, test set
# Will be split in terms of patients, not sleep data
num_patients = len(PATIENTS)

print(num_patients)
'''
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
'''