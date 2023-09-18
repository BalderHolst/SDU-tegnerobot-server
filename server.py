#! /usr/bin/env python

from flask import *
import json
import serial.tools.list_ports
from multiprocessing import Manager
import gunicorn.app.base 

# Modul som sender til printeren
import serial_interface as si

title = "Tegnerobot Server"
app = Flask(title)

class Printer:

    @classmethod
    def next_id(Self):
        global printers
        used_ids = [p.id for p in printers]
        id = 1;
        while id in used_ids:
            id += 1
        return id


    def __init__(self, port):
        self.port = port
        self.status = "idle"
        self.id = Printer.next_id()

    def __repr__(self):
        return f"Printer(id: {self.id}, port: {self.port}, status: {self.status})"

@app.route("/test")
def add_dummy_printer():
    printers.append(Printer("Dummy"))
    return site()

@app.route("/")
def site():
    js = url_for('static', filename='index.js');
    css = url_for('static', filename='index.css');
    return render_template("index.html", title=title, js_path=js, css_path=css)

# Endpoint to fetch all printers and their status
@app.route("/printers")
def json_printers():
    def to_json(p):
        return p.__dict__
    json_printers = [to_json(printer) for printer in printers]
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
    printers = manager.list(new_printers)

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

# Returns a type of the printer's intex into `printers' and the printer itself
def get_printer_by_id(id):
    for (i, p) in enumerate(printers):
        if p.id == id:
            return (i, p)
    return None

@app.route("/printers/<path:path>", methods=['POST'])
def upload_to_printer(path):

    # Try to convert the path to an id.
    try:
        id = int(path)
    except ValueError as e:
        flash(f"Endpoint `{path}` was not a printer id.")
        return redirect("/")
    (printer_index, printer) = get_printer_by_id(id)
    if not printer:
        flash(f"Could not find printer with id: `{id}`.")
        return redirect("/")

    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):

        # Update the printer status
        printer.status = "running"

        # This line is need for the Manager to update its data
        printers[printer_index] = printer

        si.send_to_printer(printer, file.read())
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
    }
    # initialize()
    HttpServer(app, options).run()

