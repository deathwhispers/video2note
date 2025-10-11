# src/video2note/downloader/base.py

from abc import ABC, abstractmethod


class VideoDownloader(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def download(self, url: str):
        """
        下载给定 url 的视频 / 音频 /截帧等，并返回 Video 对象（在 types.video 中定义）
        """
        raise NotImplementedError


class DownloaderFactory:
    @staticmethod
    def create(provider: str, config):
        provider = provider.lower()
        if provider == "youtube":
            from video2note.downloader.youtube_downloader import YouTubeDownloader
            return YouTubeDownloader(config)
        elif provider == "bilibili":
            from video2note.downloader.bilibili_downloader import BilibiliDownloader
            return BilibiliDownloader(config)
        else:
            raise ValueError(f"Unsupported video provider: {provider}")
