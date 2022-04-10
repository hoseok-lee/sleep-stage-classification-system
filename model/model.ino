#include <TensorFlowLite.h>
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "tensorflow/lite/version.h"

#include "model.h"

namespace {
tflite::ErrorReporter* error_reporter = nullptr;
const tflite::Model* model = nullptr;
tflite::MicroInterpreter* interpreter = nullptr;
TfLiteTensor* input = nullptr;
TfLiteTensor* output = nullptr;
int inference_count = 0;

constexpr int kTensorArenaSize = 2000;
uint8_t tensor_arena[kTensorArenaSize];
}

void setup()
{
  Serial.begin(38400);
  while (!Serial);

  // Set up logging
  static tflite::MicroErrorReporter micro_error_reporter;
  error_reporter = &micro_error_reporter;

  model = tflite::GetModel(g_model);
  if (model->version() != TFLITE_SCHEMA_VERSION) {
    TF_LITE_REPORT_ERROR(error_reporter,
                         "Model provided is schema version %d not equal "
                         "to supported version %d.",
                         model->version(), TFLITE_SCHEMA_VERSION);
    return;
  }

  TfLiteStatus allocate_status = interpreter->AllocateTensors();
  if (allocate_status != kTfLiteOk) {
    TF_LITE_REPORT_ERROR(error_reporter, "AllocateTensors() failed");
    return;
  }

  // Obtain pointers to the model's input and output tensors.
  input = interpreter->input(0);
  output = interpreter->output(0);
  
  Serial.print("Model loaded.");
}

#define INPUT_SIZE 10
#define OUTPUT_SIZE 6

float raw_data[INPUT_SIZE];
int time_frame = 0;

void loop()
{
  // Wait for input
  while (!Serial.available());

  // Receive both data
  // Since the EEG and ECG data are comma separated, 
  // Serial.parseFloat() will first read  EEG and then ECG
  raw_data[time_frame] = Serial.parseFloat();

  // At this point both EEG and ECG data has been read
  // This is the point of separation between time frames
  // Once a complete batch has been read...
  if (time_frame == 9)
  {
    int8_t data_quantized[INPUT_SIZE];
    for (int i = 0; i < INPUT_SIZE; ++i)
    {
      data_quantized[i] = raw_data[i] / input->params.scale + input->params.zero_point;
      input->data.int8[i] = data_quantized[i];
    }

    // Run inference, and report any error
    TfLiteStatus invoke_status = interpreter->Invoke();
    if (invoke_status != kTfLiteOk) {
      TF_LITE_REPORT_ERROR(error_reporter, "Invoke failed\n");
      Serial.print("Error invoking\n");
      return;
    }

    int8_t raw_output[OUTPUT_SIZE];
    // Obtain the quantized output from model's output tensor
    for (int i = 0; i < OUTPUT_SIZE; ++i)
    {
      // Quantized
      raw_output[i] = output->data.int8[i];
      // Dequantize the output from integer to floating-point
      raw_output[i] = (raw_output[i] - output->params.zero_point) * output->params.scale;
      Serial.print(String(raw_output[i]) + "\n");
    }
      
    // Read the other data on the next iteration
    time_frame = 0;
  }
  else
  {
    // Move onto the next time frame
    time_frame += 1;
  }
}
