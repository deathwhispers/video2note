import os
import subprocess
from src.utils import ensure_dir, load_config, logger

# -------------------------------
# 音频提取
# -------------------------------
def extract_audio(video_path, output_dir):
    """
    使用 ffmpeg 从视频中提取音频
    """
    ensure_dir(output_dir)
    audio_file = os.path.join(output_dir, "audio.wav")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",  # 去掉视频流
        "-acodec", "pcm_s16le",
        "-ar", "16000",  # 16kHz
        "-ac", "1",
        audio_file
    ]
    logger.info(f"[transcriber] 提取音频: {audio_file}")
    try:
        subprocess.run(cmd, check=True)
        return audio_file
    except Exception as e:
        logger.error(f"[transcriber] 音频提取失败: {e}")
        return None


# -------------------------------
# OpenAI Whisper 转写
# -------------------------------
def transcribe_with_openai(audio_path, config):
    import openai
    providers = config.get("providers", {})
    openai_cfg = providers.get("openai", {})
    openai.api_key = openai_cfg.get("api_key")
    language = config.get("video.language", "zh")

    with open(audio_path, "rb") as f:
        result = openai.Audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language=language
        )
    return result.text


# -------------------------------
# Mock 模式转写
# -------------------------------
def transcribe_with_mock(audio_path, config):
    logger.info(f"[transcriber] Mock 模式：返回固定文本")
    return "这是一个模拟的音频转写文本，用于测试 pipeline。"


# -------------------------------
# 其他厂商可扩展
# -------------------------------
def transcribe_with_gemini(audio_path, config):
    # TODO: 实现 Gemini API 调用
    logger.info("[transcriber] Gemini 转写暂未实现，使用 mock")
    return transcribe_with_mock(audio_path, config)

def transcribe_with_qwen(audio_path, config):
    # TODO: 实现 Qwen API 调用
    logger.info("[transcriber] Qwen 转写暂未实现，使用 mock")
    return transcribe_with_mock(audio_path, config)

def transcribe_with_ernie(audio_path, config):
    # TODO: 实现 Ernie API 调用
    logger.info("[transcriber] Ernie 转写暂未实现，使用 mock")
    return transcribe_with_mock(audio_path, config)

def transcribe_with_vllm(audio_path, config):
    # TODO: 实现 VLLM API 调用
    logger.info("[transcriber] VLLM 转写暂未实现，使用 mock")
    return transcribe_with_mock(audio_path, config)


# -------------------------------
# 统一接口
# -------------------------------
def transcribe(audio_path, config):
    """
    根据配置自动选择厂商进行转写
    """
    if config.get("app.mock", False):
        return transcribe_with_mock(audio_path, config)

    provider = config.get("ai.provider", "openai").lower()
    if provider == "openai":
        return transcribe_with_openai(audio_path, config)
    elif provider == "gemini":
        return transcribe_with_gemini(audio_path, config)
    elif provider == "qwen":
        return transcribe_with_qwen(audio_path, config)
    elif provider == "ernie":
        return transcribe_with_ernie(audio_path, config)
    elif provider == "vllm":
        return transcribe_with_vllm(audio_path, config)
    else:
        logger.warning(f"[transcriber] 未知 provider {provider}，使用 mock")
        return transcribe_with_mock(audio_path, config)


# -------------------------------
# CLI 测试
# -------------------------------
if __name__ == "__main__":
    cfg = load_config()
    video_dir = cfg.get("video.download_path", "./downloads")
    video_file = os.path.join(video_dir, "video.mp4")

    audio_file = extract_audio(video_file, video_dir)
    if audio_file:
        text = transcribe(audio_file, cfg)
        logger.info(f"\n✅ 转写结果:\n{text}")
