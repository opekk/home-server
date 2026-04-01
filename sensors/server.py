import json
import os
import threading
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import serial

SERIAL_PORT = os.environ.get("SERIAL_PORT", "/dev/ttyUSB0")
BAUD_RATE = 115200
DATA_FILE = Path("/data/latest.json")

latest_reading = {"temperature": None, "updated_at": None}


def load_persisted():
    global latest_reading
    if DATA_FILE.exists():
        try:
            latest_reading = json.loads(DATA_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass


def persist():
    try:
        DATA_FILE.write_text(json.dumps(latest_reading))
    except OSError:
        pass


def serial_reader():
    while True:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=5)
            print(f"Reading from {SERIAL_PORT}")
            while True:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if line.startswith("TEMP:"):
                    try:
                        temperature = float(line[5:])
                        latest_reading["temperature"] = temperature
                        latest_reading["updated_at"] = datetime.now(timezone.utc).isoformat()
                        latest_reading["updated_at"].strftime("%H-%M %d-%m-%Y")
                        persist()
                        print(f"Temperature updated: {temperature}")
                    except ValueError:
                        pass
        except serial.SerialException as e:
            print(f"Serial error: {e}, retrying in 5s...")
            import time
            time.sleep(5)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Temperature</title>
    <meta http-equiv="refresh" content="1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .card {
            text-align: center;
            padding: 3rem;
            background: #1e293b;
            border-radius: 1rem;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
        }
        .label { font-size: 1rem; color: #94a3b8; margin-bottom: 0.5rem; }
        .temp { font-size: 5rem; font-weight: 700; }
        .updated { font-size: 0.85rem; color: #64748b; margin-top: 1rem; }
        .no-data { font-size: 1.5rem; color: #64748b; }
    </style>
</head>
<body>
    <div class="card">
        <div class="label">Current Temperature</div>
        CONTENT
    </div>
</body>
</html>"""


class SensorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/temperature":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(latest_reading).encode())
            return

        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            if latest_reading["temperature"] is not None:
                content = f'<div class="temp">{latest_reading["temperature"]}\u00b0C</div>'
            else:
                content = '<div class="no-data">No data yet</div>'
            self.wfile.write(HTML_TEMPLATE.replace("CONTENT", content).encode())
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        print(f"{self.client_address[0]} - {format % args}")


if __name__ == "__main__":
    load_persisted()
    reader = threading.Thread(target=serial_reader, daemon=True)
    reader.start()
    server = HTTPServer(("0.0.0.0", 8000), SensorHandler)
    print("Sensors server running on port 8000")
    server.serve_forever()
