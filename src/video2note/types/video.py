# src/video2note/types/video.py

from typing import Optional, List

class DownloadedVideo:
    def __init__(
            self,
            video_path: str,
            audio_path: str,
            frame_paths: Optional[List[str]] = None,
            duration: Optional[float] = None,
            meta: Optional[dict] = None,
    ):
        self.video_path = video_path
        self.audio_path = audio_path
        self.frame_paths = frame_paths or []
        self.duration = duration
        self.meta = meta or {}
