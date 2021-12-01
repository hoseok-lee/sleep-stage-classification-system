class PatientData (object):
    ECG_signal = None
    EEG_signal = None
    sleep_stages = None

    record_length = None
    sampling_frequency = None

    def __init__ (self, patient_name):
        self.patient_name = patient_name