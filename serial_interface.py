import serial

def send_to_printer(printer, data):
    # TODO
    printer.status = "running"
    print(f"Sending to printer {printer.id}:\n{data}")
