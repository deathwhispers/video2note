import os
import yaml
import logging

# =============================
# 日志配置
# =============================
logger = logging.getLogger("video2note")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("[%(levelname)s] %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


# =============================
# 文件夹确保存在
# =============================
def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        logger.debug(f"创建目录: {path}")


# =============================
# 配置加载
# =============================
def load_config(config_path: str = "./config/config.yaml") -> dict:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    logger.debug(f"加载配置: {config_path}")
    return cfg
