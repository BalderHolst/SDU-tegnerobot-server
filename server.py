#! /usr/bin/env python

from flask import *
import json

# Modul som sender til printeren
import serial_interface as si

title = "Tegnerobot Server"
app = Flask(title)

next_id = 1
class Printer:
    def __init__(self, port):
        self.port = port
        self.status = "idle"
        global next_id
        self.id = next_id
        next_id += 1

printers = [Printer("some_port"), Printer("some_OTHER_port")]

for i in range(20):
    printers.append(Printer(f"Dummy {i}"))

# TESTING
printers[5].status = "running"
printers[6].status = "error"

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


# Iconet på tab'en
@app.route("/favicon.ico")
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))

ALLOWED_EXTENSIONS = [ 'txt', 'csv' ]
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/printers/<path:path>", methods=['POST'])
def upload_to_printer(path):

    # Try to convert the path to an id.
    try:
        id = int(path)
    except ValueError as e:
        flash(f"Endpoint `{path}` was not a printer id.")
        return site()

    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        si.send_to_printer(id, file.read())
    return redirect("/")

def run():
    app.run(host="0.0.0.0", port=5005)

if __name__ == "__main__":
    run()
