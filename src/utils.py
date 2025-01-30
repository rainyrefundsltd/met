# utils.py
import json
import os

def save_to_json(data, filename):
    """Save data to a JSON file."""
    os.makedirs("data", exist_ok=True)
    filepath = os.path.join("data", filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {filepath}")

def read_json(filename):
    """Read data from a JSON file."""
    filepath = os.path.join("data", filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File {filepath} not found.")
    with open(filepath, "r") as f:
        return json.load(f)

def log_message(message):
    """Log a message to the console."""
    print(f"[LOG] {message}")
