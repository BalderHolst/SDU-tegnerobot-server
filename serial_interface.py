import serial

def send_to_printer(printer, file):
    data = file.read()
    printer.status = "running"
    print(f"Sending '{file.filename}' to printer {printer.id}.\n{data}")
