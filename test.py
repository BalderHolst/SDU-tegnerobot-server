import server

PORT = "/dev/ttyACM0"

p = server.Printer(PORT);
p.send_text("hello from python")
