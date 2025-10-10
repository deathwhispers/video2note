import os
import subprocess
from pathlib import Path

from src.utils import ensure_dir, logger


# -------------------------------
# 音频提取
# -------------------------------
def extract_audio(video_file, audio_dir):
    ensure_dir(audio_dir)

    # 生成与视频同名的音频文件名（替换扩展名为.wav）
    audio_filename = Path(video_file).stem + ".wav"
    audio_file = os.path.join(audio_dir, audio_filename)  # 完整音频路径

    cmd = [
        "ffmpeg", "-y",
        "-i", video_file,
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1",
        audio_file
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"[transcriber] 音频提取完成: {audio_file}")
        return audio_file
    except Exception as e:
        logger.error(f"[transcriber] 音频提取失败: {e}")
        return None


# -------------------------------
# 关键帧提取
# -------------------------------
def extract_key_frames(video_file, output_dir, interval=10):
    ensure_dir(output_dir)
    frames = []
    cmd = [
        "ffmpeg", "-y",
        "-i", video_file,
        "-vf", f"fps=1/{interval}",  # 每interval秒一帧
        "-q:v", "2",  # 画质等级
        os.path.join(output_dir, "frame_%04d.jpg")
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        # 收集帧路径
        for f in os.listdir(output_dir):
            if f.startswith("frame_") and f.endswith(".jpg"):
                frames.append(os.path.join(output_dir, f))
        logger.info(f"[transcriber] 提取关键帧 {len(frames)} 张")
        return frames
    except Exception as e:
        logger.error(f"[transcriber] 帧提取失败: {e}")
        return []


# -------------------------------
# 转写接口（多厂商支持）
# -------------------------------
def transcribe_with_openai(audio_path, config):
    from openai import OpenAI

    openai_cfg = config.get("providers", {}).get("openai", {})
    api_key = openai_cfg.get("api_key")
    if not api_key:
        raise ValueError("OpenAI API 密钥未配置（providers.openai.api_key）")
    # 初始化客户端（新版本必须创建客户端实例）
    client = OpenAI(api_key=api_key)
    language = config.get("video", {}).get("language", "zh")
    model = config.get("ai", {}).get("model", {})

    logger.info(f"[transcriber] 使用模型 {model} 进行转写")

    try:
        with open(audio_path, "rb") as f:
            # 新版本 API 调用方式（通过 client 实例）
            result = client.audio.transcriptions.create(
                model=model,
                file=f,
                language=language
            )
        return result.text
    except Exception as e:
        logger.error(f"[transcriber] OpenAI 转写失败：{str(e)}")
        raise


def transcribe_with_whisper_local(audio_path, config):
    """本地Whisper模型转写音频（无需API）"""
    import whisper

    # 选择模型（tiny/base/small/medium/large，越小速度越快，精度越低）
    model_name = config.get("ai", {}).get("whisper_model", "base")  # 推荐"base"平衡速度和精度
    model = whisper.load_model(model_name)  # 本地加载模型（首次运行会自动下载）

    logger.info(f"[transcriber] 本地Whisper模型 {model_name} 开始转写...")
    result = model.transcribe(
        audio_path,
        language="zh",  # 强制中文识别（避免误判语言）
        fp16=False  # 如无NVIDIA GPU，设为False（用CPU运行）
    )
    return result["text"]  # 返回转写文本


def transcribe_with_local(audio_path, config):
    local_cfg = config.get("providers", {}).get("local", {})
    transcriber = local_cfg.get("transcriber", "whisper")
    if transcriber == "whisper":
        return transcribe_with_whisper_local(audio_path, config)
    else:
        logger.warning(f"未知local transcriber {transcriber}，使用mock")
        return transcribe_with_mock(audio_path, config)


def transcribe_with_mock(audio_path, config):
    return "这是模拟的音频转写文本（测试用）"


def transcribe_with_gemini(audio_path, config):
    logger.warning("[transcriber] Gemini转写未实现，使用mock")
    return transcribe_with_mock(audio_path, config)


def transcribe_with_qwen(audio_path, config):
    logger.warning("[transcriber] Qwen转写未实现，使用mock")
    return transcribe_with_mock(audio_path, config)


def transcribe(audio_path, config):
    if config.get("app", {}).get("mock", False):
        return transcribe_with_mock(audio_path, config)

    provider = config.get("ai", {}).get("provider", "openai").lower()
    if provider == "openai":
        return transcribe_with_openai(audio_path, config)
    elif provider == "gemini":
        return transcribe_with_gemini(audio_path, config)
    elif provider == "qwen":
        return transcribe_with_qwen(audio_path, config)
    elif provider == "local":
        return transcribe_with_whisper_local(audio_path, config)
    else:
        logger.warning(f"未知provider {provider}，使用mock")
        return transcribe_with_mock(audio_path, config)
