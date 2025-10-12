# src/video2note/config_manager/loader.py

from pathlib import Path
from types import SimpleNamespace

import yaml

from video2note.config_manager.validator import validate_config


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
    # 获取项目根目录
    project_root = Path(__file__).resolve().parents[3]

    # 如果用户指定了配置文件路径
    if config_path:
        user_path = Path(config_path)
        # 如果是相对路径，转为相对于项目根目录
        if not user_path.is_absolute():
            user_path = project_root / user_path
        if not user_path.exists():
            raise FileNotFoundError(f"用户指定配置文件不存在: {user_path}")
        cfg_path = user_path
    else:
        # 默认配置文件路径
        cfg_path = project_root / "config" / "base_config.yaml"
        if not cfg_path.exists():
            raise FileNotFoundError(f"默认配置文件不存在: {cfg_path}")


    # 加载配置文件
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # validate_config(cfg)
    return dict_to_namespace(cfg)
