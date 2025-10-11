# src/video2note/types/transcript.py

from typing import List

class Segment:
    def __init__(self, start: float, end: float, text: str, confidence: Optional[float] = None):
        self.start = start
        self.end = end
        self.text = text
        self.confidence = confidence

    def __repr__(self):
        return f"Segment({self.start:.2f}-{self.end:.2f}: {self.text})"

class Transcript:
    def __init__(self, segments: List[Segment]):
        self.segments = segments

    def get_full_text(self) -> str:
        # 拼接所有片段的 text
        return " ".join(seg.text for seg in self.segments)


