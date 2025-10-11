# src/video2note/transcriber/openai_transcriber.py

from video2note.transcriber.base import Transcriber
from video2note.types.transcript import Transcript, Segment
from video2note.core.exceptions import TranscriptionError
from video2note.utils.logger import logging

import openai  # 假设你使用 openai 库



class OpenAITranscriber(Transcriber):
    def __init__(self, config):
        super().__init__(config)
        openai_cfg = config.providers.openai  # 假定 config.providers.openai 是一个 Namespace
        self.api_key = openai_cfg.api_key
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        openai.api_key = self.api_key

        # 模型 /语言 /其他参数
        self.model = openai_cfg.model
        self.language = getattr(config.video, "language", "zh")

    def transcribe(self, audio_path: str) -> Transcript:
        logging.info(f"[OpenAITranscriber] 转写音频 {audio_path}，模型 {self.model}")
        try:
            with open(audio_path, "rb") as f:
                result = openai.Audio.transcriptions.create(
                    model=self.model,
                    file=f,
                    language=self.language
                )
            text = result.text
            # 这里假设 OpenAI 接口只返回纯文本，没有时间戳信息
            # 我们将整个文本作为一个 Segment
            seg = Segment(start=0.0, end=0.0, text=text, confidence=None)
            return Transcript([seg])
        except Exception as e:
            logging.error(f"[OpenAITranscriber] 转写失败: {e}")
            raise TranscriptionError(f"OpenAI transcribe failed: {e}")
