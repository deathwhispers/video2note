import os
import subprocess
from pathlib import Path

from utils import ensure_dir, logger


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


# 豆包转写（音频转文本）
def transcribe_with_doubao(audio_path, config):
    import requests

    doubao_cfg = config.get("providers", {}).get("doubao", {})
    api_key = doubao_cfg.get("api_key")
    endpoint = doubao_cfg.get("endpoint", "https://api.doubao.com/v1/audio/transcriptions")

    if not api_key:
        raise ValueError("豆包API密钥未配置（providers.doubao.api_key）")

    # 读取音频文件
    with open(audio_path, "rb") as f:
        audio_data = f.read()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/octet-stream"
    }
    params = {
        "language": config.get("video", {}).get("language", "zh"),
        "model": config.get("ai", {}).get("model", "doubao-6b-audio")
    }

    logger.info(f"[transcriber] 使用豆包模型 {params['model']} 转写")
    try:
        response = requests.post(
            url=endpoint,
            headers=headers,
            params=params,
            data=audio_data,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        return result.get("text", "")
    except Exception as e:
        logger.error(f"[transcriber] 豆包转写失败：{str(e)}")
        raise


# -------------------------------
# 新增：DeepSeek转写（音频转文本）
# -------------------------------
def transcribe_with_deepseek(audio_path, config):
    import requests

    deepseek_cfg = config.get("providers", {}).get("deepseek", {})
    api_key = deepseek_cfg.get("api_key")
    endpoint = deepseek_cfg.get("endpoint", "https://api.deepseek.com/v1/audio/transcribe")

    if not api_key:
        raise ValueError("DeepSeek API密钥未配置（providers.deepseek.api_key）")

    with open(audio_path, "rb") as f:
        files = {"file": f}
        data = {
            "model": config.get("ai", {}).get("model", "deepseek-audio-v1"),
            "language": config.get("video", {}).get("language", "zh")
        }
        headers = {"Authorization": f"Bearer {api_key}"}

        logger.info(f"[transcriber] 使用DeepSeek模型 {data['model']} 转写")
        try:
            response = requests.post(
                url=endpoint,
                headers=headers,
                data=data,
                files=files,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return result.get("transcription", "")
        except Exception as e:
            logger.error(f"[transcriber] DeepSeek转写失败：{str(e)}")
            raise


# -------------------------------
# 通义千问（Qwen）真实转写
# -------------------------------
def transcribe_with_qwen(audio_path: str, config: dict) -> str:
    import dashscope
    import os

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")

    qwen_cfg = config.get("providers", {}).get("qwen", {})
    api_key = qwen_cfg.get("api_key")
    if not api_key:
        raise ValueError("通义千问API密钥未配置（providers.qwen.api_key）")

    model = config.get("ai", {}).get("asr_model", "qwen-audio-v1")
    language_hint = config.get("video", {}).get("language", "zh")

    # 可选：根据语言设置提示语（提升识别准确率）
    language_prompts = {
        "zh": "请将音频内容逐字转写为中文文本，不要总结。",
        "en": "Please transcribe the audio content verbatim into English text.",
        "ja": "音声内容を逐語的に日本語テキストに書き起こしてください。",
        "ko": "오디오 내용을 한글 텍스트로 충실하게 받아쓰기 하세요."
    }
    prompt_text = language_prompts.get(language_hint, "Transcribe the audio.")

    try:
        # ✅ 正确调用方式：使用 messages + content 列表
        response = dashscope.Generation.call(
            model="paraformer-v2",
            api_key=api_key,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"audio": audio_path},
                        {"text": prompt_text}
                    ]
                }
            ]
        )
    except Exception as e:
        raise RuntimeError(f"调用通义千问 ASR 失败: {e}")

    # 解析响应
    if response.status_code == 200:
        choices = response.output.get("choices", [])
        if not choices:
            raise ValueError("ASR 返回结果为空")
        content = choices[0].get("message", {}).get("content", "").strip()
        return content
    else:
        raise RuntimeError(
            f"ASR 请求失败 [code={response.code}]: {response.message} "
            f"(request_id={response.request_id})"
        )


# 主转写函数
def transcribe(audio_path, config):
    if config.get("app", {}).get("mock", False):
        return transcribe_with_mock(audio_path, config)

    provider = config.get("ai", {}).get("provider", "openai").lower()
    if provider == "openai":
        return transcribe_with_openai(audio_path, config)
    elif provider == "qwen":
        return transcribe_with_qwen(audio_path, config)  # 替换原占位函数
    elif provider == "doubao":
        return transcribe_with_doubao(audio_path, config)  # 新增
    elif provider == "deepseek":
        return transcribe_with_deepseek(audio_path, config)  # 新增
    elif provider == "local":
        return transcribe_with_whisper_local(audio_path, config)
    else:
        logger.warning(f"未知provider {provider}，使用mock")
        return transcribe_with_mock(audio_path, config)