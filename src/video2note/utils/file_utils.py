# src/video2note/utils/file_utils.py

import os
from pathlib import Path
from typing import Any


def ensure_dir(path: str):
    p = Path(path)
    if not p.exists():
        p.mkdir(parents=True, exist_ok=True)


def replace_env_vars(obj: Any) -> Any:
    """
    递归替换 ${VAR_NAME} 为环境变量值
    """
    if isinstance(obj, dict):
        return {key: replace_env_vars(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [replace_env_vars(item) for item in obj]
    elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        # 去掉 ${ 和 }
        var_name = obj[2:-1]
        value = os.getenv(var_name)
        if value is None:
            raise ValueError(f"Environment variable '{var_name}' not set, but referenced in config.yaml")
        return value
    else:
        return obj


def write_text(path: str, text: str, encoding="utf-8"):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding=encoding) as f:
        f.write(text)


def read_text(path: str, encoding="utf-8"):
    with open(path, "r", encoding=encoding) as f:
        return f.read()
