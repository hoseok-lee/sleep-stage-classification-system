void setup() {
  Serial.begin(38400);
  while (!Serial);
}

int prediction = 0;
int next = 0;
void loop() {
  // Wait for input
  while (!Serial.available());
  
  // Receive prediction
  prediction = Serial.parseInt();
  Serial.print(String(prediction) + "\n");

  switch (prediction)
  {
    case 0:
      digitalWrite(LEDR, LOW);
      digitalWrite(LEDG, LOW);
      digitalWrite(LEDB, LOW);
      break;
    case 1:
      digitalWrite(LEDB, LOW);
      digitalWrite(LEDR, HIGH);
      digitalWrite(LEDG, HIGH);
      break;
    case 2:
      digitalWrite(LEDG, LOW);
      digitalWrite(LEDB, HIGH);
      digitalWrite(LEDR, HIGH);
      break;
    case 3:
      digitalWrite(LEDB, LOW);
      digitalWrite(LEDR, LOW);
      digitalWrite(LEDG, HIGH);
      break;
    case 4:
      digitalWrite(LEDR, LOW);
      digitalWrite(LEDG, HIGH);
      digitalWrite(LEDB, HIGH);
      break;
    case 5:
    default:
      digitalWrite(LEDR, HIGH);
      digitalWrite(LEDG, HIGH);
      digitalWrite(LEDB, HIGH);
      break;
  }
}
