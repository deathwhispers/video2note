# src/video2note/config_manager/loader.py

import os
from pathlib import Path
import yaml
from video2note.config_manager.validator import validate_config
from types import SimpleNamespace

def merge_dict(d: dict, u: dict):
    for k, v in u.items():
        if isinstance(v, dict) and k in d and isinstance(d[k], dict):
            merge_dict(d[k], v)
        else:
            d[k] = v

def dict_to_namespace(d: dict):
    ns = SimpleNamespace()
    for k, v in d.items():
        if isinstance(v, dict):
            setattr(ns, k, dict_to_namespace(v))
        else:
            setattr(ns, k, v)
    return ns

def load_config(config_path: str = None):
    # 假定配置目录在项目根 “config/”
    project_root = Path(__file__).parent.parent.parent
    base_cfg_path = project_root / "config" / "base_config.yaml"
    cfg = {}
    with open(base_cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # 根据环境变量覆盖
    env = os.getenv("VIDEO2NOTE_ENV", "dev")
    override_path = project_root / "config" / f"{env}_config.yaml"
    if override_path.exists():
        with open(override_path, "r", encoding="utf-8") as f:
            override = yaml.safe_load(f)
        merge_dict(cfg, override)

    # 用户指定的配置覆盖
    if config_path:
        user_path = Path(config_path)
        if user_path.exists():
            with open(user_path, "r", encoding="utf-8") as f:
                user_cfg = yaml.safe_load(f)
            merge_dict(cfg, user_cfg)
        else:
            raise FileNotFoundError(f"Config file {config_path} not found")

    validate_config(cfg)
    return dict_to_namespace(cfg)
