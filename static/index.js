async function get_printers() {
    let response = await fetch('/printers');
    let printers = await response.json();
    return printers;
}

// This function assumes that the printer does not already have an html element
function createPrinterElement(printer) {
    // Variable describing if the printer is available.
    let available = false;

    // Create form for submitting
    const printer_div = document.createElement("form");
    printer_div.className = "printer";
    printer_div.setAttribute("method", "post");
    printer_div.setAttribute("action", "/printers/" + printer.id);
    printer_div.setAttribute("enctype", "multipart/form-data");

    // Set the status of the printer
    if (printer.status == "idle") {
        available = true;
        printer_div.classList.add("idle");
    }
    else if (printer.status == "running") {
        printer_div.classList.add("running");
    }
    else {
        printer_div.classList.add("error");
    }

    // The html id of the printer input node
    const input_id = "printer" + printer.id;

    const input = document.createElement("input");
    input.setAttribute("id", input_id);
    input.setAttribute("style", "display: None;");
    input.setAttribute("type", "file");
    input.setAttribute("onchange", "form.submit()");
    input.setAttribute("name", "file");
    printer_div.appendChild(input); // Add the printer name to the printer node

    const label = document.createElement("label");
    if (available) {
        label.setAttribute("for", input_id);
    }
    label.textContent = "Printer: " + printer.id;
    label.className = "printer_name";

    printer_div.appendChild(label); // Add the printer name to the printer node

    return printer_div;
}

function populate_printers(printers) {
    const printers_div = document.getElementById("printers");

    if (printers.length === 0) {
        console.log("no printers")
        return
    }

    for (printer of printers) {
        printers_div.appendChild(createPrinterElement(printer))
    }
}

// TODO: Add remove old
async function update_printers() {
    const printers = await get_printers();

    for (printer of printers) {
        let label = document.getElementById("printer" + printer.id);

        var div;
        if (label === null) {
            var div = createPrinterElement(printer);
            const printers_div = document.getElementById("printers");
            printers_div.append(div);
        }
        else {
            var div = label.parentElement;
        }

        div.classList.remove("idle");
        div.classList.remove("running");
        div.classList.remove("error");

        if (printer.status == "idle") {
            div.classList.add("idle");
        }
        else if (printer.status == "running") {
            div.classList.add("running");
        }
        else {
            div.classList.add("error");
        }
    }
}

get_printers().then(printers => populate_printers(printers));

// Update printer status every 4 seconds
const intervalId = window.setInterval(update_printers, 4000);
