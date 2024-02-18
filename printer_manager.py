from enum import Enum
from dataclasses import dataclass
import multiprocessing
import serial
import time

import parsers

class PrinterStatus(Enum):
    RUNNING = 0,
    IDLE = 1,

@dataclass
class PrinterConnection:
    port: str
    serial: serial.Serial
    status: PrinterStatus


jobs_queue = multiprocessing.Queue()
ports = {}

BAUD_RATE = 9600

class SendError(Exception):
    pass


def send_file(port: str, file):
    ext = file.filename.split(".")[-1];
    msg = ""
    if ext.lower() == "csv":
        text = file.read().decode()
        msg = parsers.parse_csv_text(text);
    else:
        raise SendError(f"Extension '{ext}' not supported.")

    send_bytes(port, msg)

def send_bytes(port, bs: bytes):

    if port == None:
        print("Skipping sending to dummy printer.")
        return

    jobs_queue.put((port, bs))

def send_job(port: str, bs: bytes):

    conn = None
    if port in ports:
        print(f"Found existing serial connection to {port}")
        conn = ports[port]
    else:
        print(f"Starting new serial connection to {port}")
        serial_conn = serial.Serial(port, BAUD_RATE, timeout=2)
        print(f"Clearing '{port}'")
        serial_conn.readall() # Empty the serial buffer

        time.sleep(0.05) 

        conn = PrinterConnection(port, serial_conn, PrinterStatus.RUNNING)
        ports[port] = conn

    
    # We write twice the data twice as very simple error checking.
    # The printer will not send and "ACK" message if the two messages
    # don't match.
    print(f"Writing {conn.port}")
    conn.serial.write(bs)
    conn.serial.write(b"\n")
    conn.serial.write(bs)
    conn.serial.write(b"\n")
    time.sleep(0.05) 
    
    print(f"Reading '{conn.port}'")
    resp = conn.serial.readall()

    if resp != b"ACK\r\n":
        raise SendError(f"Printer did not recieve message correctly. Got: {resp}.")

    print(f"Sent job to '{conn.port}' successfully!")

def worker(q: multiprocessing.Queue):
    print("Starting printer manager worker...")

    while True:
        if not q.empty():
            port, bs  = q.get()
            try:
                send_job(port, bs)
            except SendError as e:
                print(f"Printer Manager Error: '{e}'")

