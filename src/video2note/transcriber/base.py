# src/video2note/transcriber/base.py
"""
Transcriber 抽象基类与辅助函数
- 提供 transcribe_file(audio_path) 以便直接传入音频路径独立调试
- 提供 extract_audio(video_path, audio_dir) 辅助（基于 ffmpeg）
"""
import logging
import os
import subprocess
import typing
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
        将单个音频文件转写为 Transcript 对象。这个方法是单独调试的入口。
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


def extract_audio(video_file: str, audio_dir: str, sample_rate: int = 16000) -> typing.Optional[str]:
    """
    从视频文件抽取音频到指定目录，返回音频文件路径（wav PCM 16k mono）。
    若失败返回 None（调用方应处理异常）。
    """
    video_file = str(video_file)
    audio_dir = str(audio_dir)
    ensure_dir(audio_dir)

    video_p = Path(video_file)
    if not video_p.exists():
        logging.error(f"[extract_audio] video file not found: {video_file}")
        return None
    audio_filename = video_p.stem + ".wav"
    audio_path = os.path.join(audio_dir, audio_filename)

    cmd = [
        "ffmpeg", "-y",
        "-i", video_file,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", str(sample_rate),
        "-ac", "1",
        audio_path
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"[extract_audio] 音频提取完成: {audio_path}")
        return audio_path
    except subprocess.CalledProcessError as e:
        logging.error(f"[extract_audio] ffmpeg 音频提取失败: {e.stderr.decode(errors='ignore') if e.stderr else e}")
        return None
    except Exception as e:
        logging.error(f"[extract_audio] failed: {e}")
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



