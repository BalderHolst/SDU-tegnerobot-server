#! /usr/bin/env python

from flask import *
import json
import serial.tools.list_ports

# Modul som sender til printeren
import serial_interface as si

title = "Tegnerobot Server"
app = Flask(title)


printers = []

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

    # We do not need the old printers any longer
    printers = new_printers

    # Add the newly connected printers
    for port in new_ports:
        print(f"Added new: {port.device}")
        printers.append(Printer(port.device))

    # Print some status
    print(f"Found {len(printers)} printers:")
    for p in printers:
        print("\t" + str(p))
        
    return redirect("/");


# Iconet på tab'en
@app.route("/favicon.ico")
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))

ALLOWED_EXTENSIONS = [ 'txt', 'csv' ]
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_printer_by_id(id):
    for p in printers:
        if p.id == id:
            return p
    return None

@app.route("/printers/<path:path>", methods=['POST'])
def upload_to_printer(path):

    # Try to convert the path to an id.
    try:
        id = int(path)
    except ValueError as e:
        flash(f"Endpoint `{path}` was not a printer id.")
        return redirect("/")
    printer = get_printer_by_id(id)
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
        si.send_to_printer(printer, file.read())
    return redirect("/")

def run():
    app.run(host="0.0.0.0", port=5005)

if __name__ == "__main__":
    scan_for_printers()
    run()
