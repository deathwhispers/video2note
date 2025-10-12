# src/video2note/transcriber/base.py

import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from utils import ensure_dir, logger
from video2note.types.transcript import Transcript


class Transcriber(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def transcribe(self, audio_path: str) -> Transcript:
        """
        转写音频文件为 Transcript。
        如果失败，应抛出 TranscriptionError。
        """
        raise NotImplementedError


class TranscriberFactory:
    @staticmethod
    def create(provider: str, config):
        prov = provider.lower()
        if prov == "openai":
            from video2note.transcriber.openai_transcriber import OpenAITranscriber
            return OpenAITranscriber(config)
        elif prov == "local_whisper":
            from video2note.transcriber.local_whisper import LocalWhisperTranscriber
            return LocalWhisperTranscriber(config)
        elif prov == "qwen":
            from video2note.transcriber.qwen_transcriber import QwenTranscriber
            return QwenTranscriber(config)
        elif prov == "doubao":
            from video2note.transcriber.doubao_transcriber import DoubaoTranscriber
            return DoubaoTranscriber(config)
        elif prov == "deepseek":
            from video2note.transcriber.deepseek_transcriber import DeepSeekTranscriber
            return DeepSeekTranscriber(config)
        elif prov == "mock":
            from video2note.transcriber.mock_transcriber import MockTranscriber
            return MockTranscriber(config)
        else:
            raise ValueError(f"Unsupported transcriber provider: {provider}")



# -------------------------------
# 音频提取
# -------------------------------
def extract_audio(video_file, config):
    audio_dir = config.get("transcriber", {}).get("audio_dir", "audio")
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



