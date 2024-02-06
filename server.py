#! /usr/bin/env python

from flask import *
import json
import serial.tools.list_ports
from multiprocessing import Manager
import gunicorn.app.base 

# Modul som sender til printeren
import serial_interface as si

# Genererer navne til printere
import namegen

title = "Tegnerobot Server"
app = Flask(title)

class Message:
    def __init__(self, text: str, color = "blue") -> None:
        self.text = text
        self.color = color

class Printer:

    @classmethod
    def test(Self):
        name = f"TEST: {namegen.assign_name()}"
        return Self("dummy_port", name)

    @classmethod
    def next_id(Self):
        global printers
        used_ids = [p.id for p in printers]
        id = 1;
        while id in used_ids:
            id += 1
        return id

    def __init__(self, port, name = None):
        self.port = port
        if name is None:
            name = namegen.assign_name()
        self.name = name
        self.status = "idle"
        self.id = Printer.next_id()

    def __repr__(self):
        return f"Printer(id: {self.id}, port: {self.port}, status: {self.status})"

@app.route("/test")
def add_dummy_printer():
    printers.append(Printer.test())
    return site()

@app.route("/")
def site():
    js = url_for('static', filename='index.js');
    css = url_for('static', filename='index.css');
    return render_template("index.html", title=title, js_path=js, css_path=css)

# Endpoint to fetch all printers and their status
@app.route("/printers")
def json_printers():
    global printers
    json_printers = [printer.__dict__ for printer in printers]
    return json.dumps(json_printers)

# Endpoint causing the server to rescan for connected printers.
@app.route("/scan")
def scan_for_printers():
    global printers
    new_printers = []
    old_ports = [p.port for p in printers]
    new_ports = list(serial.tools.list_ports.comports())

    for (i, port) in enumerate(new_ports):

        # If any printers are persistant, we want to keep them.
        try:
            # `.index()` throws a ValueError when is does not match anything.
            index = old_ports.index(port.device)

            # add the persistant printer to the new printers 
            new_printers.append(printers[index])

            # delete then new port entry, so we do not add it again
            del new_ports[i]

        except ValueError:
            pass

    # We do not need the old printer list anymore
    for i in range(len(printers)):
        print(f"Deleting Printer: {printers[0]}")
        del printers[0]

    printers.extend(new_printers)

    # Add the newly connected printers
    for port in new_ports:
        printers.append(Printer(port.device))

    # Print some status
    print(f"Found {len(printers)} printers:")
    for p in printers:
        print("\t" + str(p))
        
    return redirect("/")


# Iconet på tab'en
@app.route("/favicon.ico")
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))

ALLOWED_EXTENSIONS = [ 'txt', 'csv' ]
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_printer_by_id(id):
    for (i, p) in enumerate(printers):
        if p.id == id:
            return (i, p)
    return None


def upload_error(e: str, printer_name = "printer"):
    print(f"UPLOAD ERROR: {e}")
    css = url_for('static', filename='index.css');
    error_css = url_for('static', filename='error.css');
    return render_template("error.html", title=title, main_css=css, error_css=error_css, printer=printer_name, message=Message(e, "#FF8888"))

@app.route("/printers/<path:path>", methods=['GET'])
def back(path):
    print(f"Redirecting GET for '/printer/{path}' to '/'")
    return redirect("/")

@app.route("/printers/<path:path>", methods=['POST'])
def upload_to_printer(path):

    # Try to convert the path to an id.
    try:
        id = int(path)
    except ValueError as _:
        return upload_error(f"Endpoint `{path}` was not a printer id.")

    res = get_printer_by_id(id)

    if not res:
        return upload_error('Printer does not exist anymore.')

    (printer_index, printer) = res
    if not printer:
        return upload_error(f"Could not find printer with id: `{id}`.")

    if 'file' not in request.files:
        return upload_error('No file part', printer.name)

    file = request.files['file']

    if file.filename == '':
        return upload_error('No selected file', printer.name)

    if file and allowed_file(file.filename):

        # Update the printer status
        printer.status = "running"

        # This line is need for the Manager to update its data
        printers[printer_index] = printer

        try:
            si.send_to_printer(printer, file)
        except Exception as e:
            printer.status = "idle"
            printers[printer_index] = printer
            return upload_error(e, printer.name)


    else:
        return upload_error(f"Filetype of '{file.filename}' not permitted. Permitted file types: {ALLOWED_EXTENSIONS}", printer.name)

    return redirect("/")

# Custom Gunicorn application: https://docs.gunicorn.org/en/stable/custom.html
class HttpServer(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

def initialize():
    global printers
    printers = manager.list()
    scan_for_printers()


if __name__ == "__main__":
    global manager
    manager = Manager()

    initialize()

    # Server options
    options = {
        'bind': '%s:%s' % ('0.0.0.0', 5005),
        'workers': 4,
        'log-level': 'debug',
        'debug': True,
        'capture-output': False,
    }
    # initialize()
    HttpServer(app, options).run()

