async function get_printers() {
    let response = await fetch('/printers');
    let printers = await response.json();
    return printers;
}


function populate_printers(printers) {
    const printers_div = document.getElementById("printers");
    for (printer of printers) {

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

        // Add the printer to its parrent node
        printers_div.appendChild(printer_div);


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


        console.log(printer);
    }
}

get_printers().then(printers => populate_printers(printers));
