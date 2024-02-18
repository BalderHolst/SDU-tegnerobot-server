from csv import excel
from enum import Enum
from dataclasses import dataclass
import multiprocessing
import serial
import time

import parsers

def log(s: str):
    print(f"[Printer Manager]: {s}")

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
        log("Skipping sending to dummy printer.")
        return

    jobs_queue.put((port, bs))

def send_job(port: str, bs: bytes):

    conn = None
    if port in ports:
        log(f"Found existing serial connection to {port}")
        conn = ports[port]
    else:
        log(f"Starting new serial connection to {port}")
        try:
            serial_conn = serial.Serial(port, BAUD_RATE, timeout=2)
        except serial.serialutil.SerialException:
            log(f"Unable to open port {port}. Aborting.")
            return
        log(f"Clearing '{port}'")
        serial_conn.readall() # Empty the serial buffer

        time.sleep(0.05) 

        conn = PrinterConnection(port, serial_conn, PrinterStatus.RUNNING)
        ports[port] = conn


    try:
        # We write twice the data twice as very simple error checking.
        # The printer will not send and "ACK" message if the two messages
        # don't match.
        log(f"Writing {conn.port}")
        conn.serial.write(bs)
        conn.serial.write(b"\n")
        conn.serial.write(bs)
        conn.serial.write(b"\n")
        time.sleep(0.05) 

    except serial.serialutil.SerialException:
        log(f"Could not write to port '{port}'. Deleting connection.")
        del ports[port]
        send_job(port, bs) # Try again
        return
    
    log(f"Reading '{conn.port}'")
    resp = conn.serial.readall()

    if resp != b"ACK\r\n":
        raise SendError(f"Printer did not recieve message correctly. Got: {resp}.")

    log(f"Sent job to '{conn.port}' successfully!")

def worker(q: multiprocessing.Queue):
    log("Starting printer manager worker...")

    while True:
        if not q.empty():
            port, bs  = q.get()
            try:
                send_job(port, bs)
            except SendError as e:
                log(f"Printer Manager Error: '{e}'")
        else:
            time.sleep(0.5)
