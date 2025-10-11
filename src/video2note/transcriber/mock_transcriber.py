# src/video2note/transcriber/mock_transcriber.py

from video2note.transcriber.base import Transcriber
from video2note.types.transcript import Transcript, Segment

class MockTranscriber(Transcriber):
    def __init__(self, config):
        super().__init__(config)

    def transcribe(self, audio_path: str) -> Transcript:
        # 模拟文本作为转写结果
        return Transcript([Segment(0.0, 0.0, "这是模拟的音频转写文本")])
