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
                        if log_entry.get("eventid") == "cowrie.login.failed":
                            message = f"Failed login attempt detected!\n" \
                                      f"IP: {log_entry.get('src_ip')}\n" \
                                      f"Username: {log_entry.get('username')}\n" \
                                      f"Password: {log_entry.get('password')}"
                            send_mattermost_alert(message)
                    except json.JSONDecodeError:
                        pass
                    line = f.readline()

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
