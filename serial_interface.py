from server import Printer

BAUD_RATE = 9600

import serial

class SendError(Exception):
    pass

def send_to_printer(printer: Printer, file):

    text = file.read()

    if printer.port == "dummy_port":
        return

    conn = serial.Serial(printer.port, BAUD_RATE, timeout=5)

    print(f"Sending '{file.filename}' to printer {printer.name}.")
    conn.write(text)
    
    resp = conn.readline()
    print(f"Response from {printer.name}")

