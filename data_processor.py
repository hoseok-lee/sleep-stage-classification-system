import os
import wfdb
import numpy as np
from dotenv import load_dotenv
from models import PatientData

load_dotenv()

# MIT-BIH polysomongraphic database tracks 6 sleep stages, while we only track 5
# This can help the performance of our final model as it allows some discrepancies between NREM 3 and NREM 4
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

# Since annotations only have labels and the time at which they occur, interpolate all the data so there's always a 
# label at each time step; one-to-one correlation between EEG/ECG signal and a classification at any point in time
def step_interpolation (data, locations, total_length):
    step_interpolated_data = np.zeros(total_length)

    for i in range(len(locations) - 1):
        start_range = locations[i]
        end_range = locations[i + 1]

        # Convert string annotation into sleep stage
        step_interpolated_data[(start_range - 1) : end_range] = annotation_sleep_stage(data[i])

    return step_interpolated_data

def get_patients ():
    with open(os.path.join(os.getenv('DATABASE_PATH'), 'RECORDS'), 'r') as file:
        patients = {
            patient_name: PatientData(patient_name)
            for patient_name in file.read().split('\n')[:-1]
        }

    # Populate patient data from database
    for patient_name in patients.keys():
        patient = patients[patient_name]

        # Retrieve raw signals and annotations
        record_path = os.path.join(os.getenv('DATABASE_PATH'), patient_name)
        record = wfdb.io.rdrecord(record_path)
        annotation = wfdb.rdann(record_path, extension='st')

        # Sampling frequency
        # This might differ for each record
        patient.sampling_frequency = record.fs

        # 0 and 2 are ECG and EEG respectively
        patient.ECG_signal = record.p_signal[:, 0]
        patient.EEG_signal = record.p_signal[:, 2]
        patient.record_length = record.sig_len

        # Stretch out sleep stage classification
        patient.sleep_stages = step_interpolation(annotation.aux_note, annotation.sample, patient.record_length)

    return patients