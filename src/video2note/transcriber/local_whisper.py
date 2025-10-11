from video2note.transcriber.base import Transcriber
from video2note.types.transcript import Transcript, Segment
from video2note.core.exceptions import TranscriptionError
from video2note.utils.logger import logging

import whisper

class LocalWhisperTranscriber(Transcriber):
    def __init__(self, config):
        super().__init__(config)
        cfg = config.providers.local
        self.model_name = cfg.whisper_model
        # 你可以为 local 还设置别的参数
        logging.info(f"[LocalWhisperTranscriber] 模型名称: {self.model_name}")

    def transcribe(self, audio_path: str) -> Transcript:
        logging.info(f"[LocalWhisperTranscriber] 转写音频 {audio_path} 使用本地 whisper")
        try:
            model = whisper.load_model(self.model_name)
            result = model.transcribe(
                audio_path,
                language="zh",
                fp16=False
            )
            text = result.get("text", "")
            seg = Segment(start=0.0, end=0.0, text=text)
            return Transcript([seg])
        except Exception as e:
            logging.error(f"[LocalWhisperTranscriber] 转写失败: {e}")
            raise TranscriptionError(f"Local whisper transcribe failed: {e}")
