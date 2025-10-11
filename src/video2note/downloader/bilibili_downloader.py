# src/video2note/downloader/bilibili_downloader.py

import asyncio
import os
from pathlib import Path
from typing import Optional, List

import bilix.sites.bilibili.api
from bilix.exception import APIError, APIResourceError, APIUnsupportedError
from bilix.sites.bilibili import DownloaderBilibili

from utils import ensure_dir, logger
from video2note.downloader.base import VideoDownloader
from video2note.types.video import DownloadedVideo


class BilibiliDownloader(VideoDownloader):
    def __init__(self, config):
        """
        config 是加载后的配置对象，
        你可以在 config 中添加如下子配置：
          config.video.download_path 或 config.video.output_dir
          config.video.frame_interval (如果你以后要截帧)
          config.bilibili.cookies_path 或其他 bilix /B 站相关配置
        """
        super().__init__(config)
        # 取你配置中视频保存目录
        self.download_path = Path(config.video.download_path)
        # 取你可能设置的帧间隔（以后截帧使用，可选）
        self.frame_interval = getattr(config.video, "frame_interval", None)
        # Bilibili 特定配置，比如 cookies
        self.cookies_path: Optional[str] = getattr(config.bilibili, "cookies_path", None)

    def download(self, url: str) -> DownloadedVideo:
        """
        同步接口（对外），内部调用异步代码。
        将下载的视频文件 /音频 /（可选帧）封装为 DownloadedVideo 返回。
        """
        # 确保目录存在
        ensure_dir(str(self.download_path))

        # 异步执行主下载逻辑
        video_files = asyncio.run(self._download_bilibili_video_async(url))

        # video_files 是一个按顺序的视频文件列表（完整视频 /分P视频文件们）
        # 在这里，我们可以选择封装路径返回，或者更“简单”返回列表路径。
        # 我们在此封装一个 DownloadedVideo，让它包含 video_files 列表作为 “meta” 或 frames
        # 假定你未来还要对 audio /截帧 /摘要 /合并等做操作，所以封装更灵活。

        # For simplicity：假设你不做音频 /截帧，那么 DownloadedVideo.video_path 可以设置为第一个视频文件，
        # audio_path = None, frame_paths = None, duration = None

        video_paths = video_files  # List[str]

        # 这里你可以选第一个作为主 video_path
        primary = video_paths[0]
        return DownloadedVideo(
            video_path=primary,
            audio_path="",
            frame_paths=video_paths,
            duration=None,
            meta={"all_video_paths": video_paths}
        )



    async def _download_bilibili_video_async(self, url: str) -> List[str]:
        """
        利用你写的 async download_bilibili_video + walk 目录逻辑，返回视频文件路径列表。
        """
        d = DownloaderBilibili()
        # 确保根目录存在
        ensure_dir(str(self.download_path))

        try:
            # 1. 先获取视频基础信息，判断是单P还是合集
            logger.info(f"[BilibiliDownloader] 解析视频信息：{url}")
            video_info = await bilix.sites.bilibili.api.get_video_info(d.client, url)

            # 2. 根据分P数量选择API：pages长度>1则为合集，调用get_series；否则调用get_video
            if len(video_info.pages) > 1:
                logger.info(f"[BilibiliDownloader] 检测到合集，分P数 {len(video_info.pages)}，使用get_series下载")
                await d.get_series(
                    url=url,
                    path=self.download_path,
                    quality=80,  # 720p（非会员可用）
                    subtitle=True,  # 下载字幕
                    image=False,  # 不下载封面
                    p_range=None  # 下载全部分P（如需指定范围可传(1,3)下载P1-P3）
                )
            else:
                logger.info(f"[BilibiliDownloader] 检测到单P视频，使用get_video下载")
                # 调用单视频下载API
                await d.get_video(
                    url=url,
                    path=self.download_path,
                    quality=80,
                    subtitle=True,
                    image=False
                )
            logger.info(f"[BilibiliDownloader] 下载完成至 {self.download_path}")

        except (APIResourceError, APIUnsupportedError) as e:
            logger.error(f"[BilibiliDownloader] 资源错误：{e}")
            raise
        except APIError as e:
            logger.error(f"[BilibiliDownloader] API 错误：{e}")
            raise
        except Exception as e:
            logger.error(f"[BilibiliDownloader] 下载异常：{e}")
            raise
        finally:
            await d.aclose()

        # 下载完成后，收集所有视频文件（按创建时间排序，确保分P顺序）
        video_extensions = (".mp4", ".flv", ".mkv")
        found = []
        for root, _, files in os.walk(self.download_path):
            for f in files:
                if f.lower().endswith(video_extensions):
                    found.append(os.path.join(root, f))

        # 按创建时间排序（或你原先逻辑的排序准则）
        found.sort(key=lambda x: os.path.getctime(x))
        if not found:
            raise FileNotFoundError(f"下载目录 {self.download_path} 中未找到视频文件")
        logger.info(f"[BilibiliDownloader] 共找到 {len(found)} 个视频文件（按分P顺序）")
        return found

