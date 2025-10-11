# src/video2note/config_manager/validator.py

def validate_config(cfg: dict):
    # 简单示例：检查必须字段
    if "video" not in cfg:
        raise ValueError("config must have 'video' section")
    if "provider" not in cfg["video"]:
        raise ValueError("config.video.provider is required")
    if "url" not in cfg["video"]:
        raise ValueError("config.video.url is required")
    if "transcriber" not in cfg:
        raise ValueError("config must have 'transcriber' section")
    if "provider" not in cfg["transcriber"]:
        raise ValueError("config.transcriber.provider is required")
    # 你可以增加更多校验（like 支持厂商、类型检查、互斥等）
