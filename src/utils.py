import os
import yaml
import datetime

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"[utils] Created directory: {path}")

def timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
