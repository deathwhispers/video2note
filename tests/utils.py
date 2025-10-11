import logging
import os
from typing import Dict, Any

import pysrt
import yaml
import ass


def ensure_dir(path):
    """确保目录存在"""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def replace_env_vars(obj: Any) -> Any:
    """递归替换 ${VAR_NAME} 为环境变量值"""
    if isinstance(obj, dict):
        return {key: replace_env_vars(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [replace_env_vars(item) for item in obj]
    elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        var_name = obj[2:-1]  # 去掉 ${ 和 }
        value = os.getenv(var_name)
        if value is None:
            raise ValueError(f"Environment variable '{var_name}' not set, but referenced in config.yaml")
        return value
    else:
        return obj

# 加载 config.yaml 配置文件（支持环境变量替换）
def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return replace_env_vars(config)


def parse_subtitles(video_dir):
    """解析字幕文件（支持.srt/.ass），返回纯文本内容"""
    subtitles = []
    for root, _, files in os.walk(video_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                if file.endswith(".srt"):
                    # 解析.srt字幕
                    subs = pysrt.open(file_path)
                    text = "\n".join([sub.text for sub in subs])  # 提取纯文本（去掉时间轴）
                    subtitles.append({"path": file_path, "content": text})
                elif file.endswith(".ass"):
                    # 解析.ass字幕（使用ass库）
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        ass_doc = ass.parse(f)  # 解析ass文件
                        # 提取对话文本（过滤空行和样式标记）
                        dialogues = []
                        for event in ass_doc.events:
                            # 忽略样式标记（如{\c&HFFFFFF&}）和空文本
                            clean_text = event.text.strip()
                            if clean_text and not clean_text.startswith("{"):
                                dialogues.append(clean_text)
                        text = "\n".join(dialogues)
                        subtitles.append({"path": file_path, "content": text})
            except Exception as e:
                logger.warning(f"解析字幕 {file_path} 失败：{e}")
    return subtitles if subtitles else None


# -------------------------------
# 日志系统
# -------------------------------
logger = logging.getLogger("video2note")
logger.setLevel(logging.INFO)

# 控制台输出
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
