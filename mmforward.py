import json
import requests
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Mattermost webhook URL
MATTERMOST_WEBHOOK_URL = "https://your-mattermost-instance/hooks/your-webhook-id"

# Path to Cowrie log file
COWRIE_LOG_PATH = "/path/to/cowrie/log/cowrie.json"

def send_mattermost_alert(message):
    payload = {
        "text": message
    }
    response = requests.post(MATTERMOST_WEBHOOK_URL, json=payload)
    if response.status_code != 200:
        print(f"Failed to send alert to Mattermost. Status code: {response.status_code}")

class CowrieLogHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == COWRIE_LOG_PATH:
            with open(COWRIE_LOG_PATH, "r") as f:
                f.seek(0, 2)  # Move to the end of the file
                line = f.readline()
                while line:
                    try:
                        log_entry = json.loads(line)
                        message = self.create_alert_message(log_entry)
                        if message:
                            send_mattermost_alert(message)
                    except json.JSONDecodeError:
                        pass
                    line = f.readline()

    def create_alert_message(self, log_entry):
        event_id = log_entry.get("eventid")
        if event_id.startswith("cowrie."):
            message = f"SSH Activity Detected: {event_id}\n"
            message += f"IP: {log_entry.get('src_ip')}\n"

            if event_id in ["cowrie.login.success", "cowrie.login.failed"]:
                message += f"Username: {log_entry.get('username')}\n"
                message += f"Password: {log_entry.get('password')}\n"
            elif event_id == "cowrie.session.connect":
                message += f"Protocol: {log_entry.get('protocol')}\n"
            elif event_id == "cowrie.command.input":
                message += f"Command: {log_entry.get('input')}\n"
            elif event_id == "cowrie.client.version":
                message += f"Version: {log_entry.get('version')}\n"
            elif event_id == "cowrie.client.size":
                message += f"Width: {log_entry.get('width')}, Height: {log_entry.get('height')}\n"
            elif event_id == "cowrie.session.file_download":
                message += f"File: {log_entry.get('url')}\n"
            elif event_id == "cowrie.session.closed":
                message += f"Duration: {log_entry.get('duration')} seconds\n"

            return message
        return None

if __name__ == "__main__":
    event_handler = CowrieLogHandler()
    observer = Observer()
    observer.schedule(event_handler, path=COWRIE_LOG_PATH, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
