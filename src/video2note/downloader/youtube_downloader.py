# src/video2note/downloader/youtube_downloader.py

from video2note.downloader.base import VideoDownloader
from video2note.types.video import DownloadedVideo


class YouTubeDownloader(VideoDownloader):
    def __init__(self, config):
        super().__init__(config)
        # 你原来的 YouTube 下载配置可以拿进来，比如 api_key,保存目录等

    def download(self, url: str) -> DownloadedVideo:
        # 这里写你原先在 downloader.py 中对 YouTube 的逻辑
        # 例如用 pytube / youtube_dl / yt-dlp 实现视频下载
        # 然后提取音频 /生成音频文件路径 /截帧等
        # 返回 DownloadedVideo 对象
        raise NotImplementedError
