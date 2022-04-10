import serial
import csv

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

random_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

while True:
    # Found an input, print it
    while ser.in_waiting:
        response = ser.readline().decode()
        writer.writerow([response]) 
        csv_file.flush()

    # Feed data to Arduino
    if random_data:
        data = random_data.pop(0)
        ser.write((str(data) + "\n").encode())
        print("Sending {}...".format(data))