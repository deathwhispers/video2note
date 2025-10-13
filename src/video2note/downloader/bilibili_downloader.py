# src/video2note/downloader/bilibili_downloader.py

import asyncio
import logging
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
        self.project_root = Path(__file__).resolve().parents[3]
        cfg_path = getattr(config.video, "download_path", "downloads")
        self.download_root = Path(cfg_path)

        if not self.download_root.is_absolute():
            self.download_root = (self.project_root / self.download_root).resolve()

        # 取你可能设置的帧间隔（以后截帧使用，可选）
        self.frame_interval = getattr(config.video, "frame_interval", 10)
        self.quality = getattr(config.video, "quality", "best")
        logging.info(f"[BilibiliDownloader] download_root = {self.download_root}")
        # Bilibili 特定配置，比如 cookies
        self.cookies_path: Optional[str] = getattr(config.video.login, "cookies_path", None)



    def download(self, url: str) -> DownloadedVideo:
        """
        同步接口（对外），内部调用异步代码。
        将下载的视频文件 /音频 /（可选帧）封装为 DownloadedVideo 返回。
        """
        ensure_dir(self.download_root)

        # 异步执行主下载逻辑
        video_files = asyncio.run(self._download_bilibili_video_async(url))

        # video_files 为按顺序的分P视频路径列表
        primary = video_files[0] if video_files else None

        return DownloadedVideo(
            video_path=primary,
            audio_path="",
            frame_paths=video_files,
            duration=None,
            meta={"all_video_paths": video_files}
        )

    async def _download_bilibili_video_async(self, url: str) -> List[str]:
        """
        内部异步下载实现，依赖 bilix DownloaderBilibili（如果可用）。
        下载路径组织：
            {download_root}/{video_id}/{files...}
        返回: 所有视频文件的完整路径列表（按创建时间排序）
        """

        if DownloaderBilibili is None:
            raise RuntimeError("bilix DownloaderBilibili is not available. Please install bilix.")

        d = DownloaderBilibili()

        # 获取视频信息用于命名（bvid /aid /title）
        try:
            logging.info(f"[BilibiliDownloader] 解析视频信息: {url}")
            video_info = await bilix.sites.bilibili.api.get_video_info(d.client, url)
        except Exception as e:
            logging.error(f"[BilibiliDownloader] 解析视频信息失败: {e}")
            raise

        # 构造输出目录
        vid = getattr(video_info, "bvid", None) or getattr(video_info, "aid", None) or "unknown_video"
        safe_vid = str(vid)
        out_base = (self.download_root / safe_vid).resolve()
        ensure_dir(out_base)

        logging.info(f"[BilibiliDownloader] download base dir: {out_base}")

        try:
            # 如果多分P，使用 get_series，否则 get_video
            pages = getattr(video_info, "pages", []) or []

            # 2. 根据分P数量选择API：pages长度>1则为合集，调用get_series；否则调用get_video
            if len(video_info.pages) > 1:
                logger.info(f"[BilibiliDownloader] 检测到合集，分P数 {len(video_info.pages)}，使用get_series下载")
                await d.get_series(
                    url=url,
                    path=out_base,
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
                    path=out_base,
                    quality=80,
                    subtitle=True,
                    image=False
                )
            logger.info(f"[BilibiliDownloader] 下载完成至 {out_base}")

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
            try:
                await d.aclose()
            except Exception:
                pass

        # 收集所有视频文件（只查 out_base）
        video_extensions = (".mp4", ".flv", ".mkv", ".webm")
        found: List[str] = []
        for root, _, files in os.walk(out_base):
            for f in files:
                if f.lower().endswith(video_extensions):
                    found.append(os.path.join(root, f))
        # 按创建时间排序（先下载的在前）
        found.sort(key=lambda x: os.path.getctime(x))
        if not found:
            raise FileNotFoundError(f"下载目录 {out_base} 中未找到视频文件")

        logger.info(f"[BilibiliDownloader] 共找到 {len(found)} 个视频文件（按分P顺序）")
        return found

