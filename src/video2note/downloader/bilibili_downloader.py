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
        self.cookies_path: Optional[str] = getattr(config.video.login, "cookies_path", None)

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
            frame_paths=[],
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


def download(self, url: str) -> DownloadedVideo:
    """
    同步接口（对外），内部调用异步代码。
    将下载的视频文件 /音频 /（可选帧）封装为 DownloadedVideo 返回。
    """
    ensure_dir(str(self.download_path))
    video_files = asyncio.run(self._download_bilibili_video_async(url))
    video_paths = video_files

    primary = video_paths[0] if video_paths else ""
    return DownloadedVideo(
        video_path=primary,
        audio_path="",
        frame_paths=[],
        duration=None,
        meta={"all_video_paths": video_paths}
    )


async def _download_bilibili_video_async(self, url: str) -> List[str]:
    """
    优化点：
    1. 下载前检查文件是否已存在，避免重复下载
    2. 基于视频元信息的分P顺序排序，替代创建时间排序
    3. 支持增量下载（仅下载缺失的分P）
    """
    d = DownloaderBilibili()
    ensure_dir(str(self.download_path))

    try:
        # 1. 获取视频元信息（关键：用于识别分P和匹配文件）
        logger.info(f"[BilibiliDownloader] 解析视频信息：{url}")
        video_info = await bilix.sites.bilibili.api.get_video_info(d.client, url)
        total_pages = len(video_info.pages)
        logger.info(f"[BilibiliDownloader] 共检测到 {total_pages} 个分P")

        # 2. 检查已存在的文件（基于分P元信息匹配）
        existing_indices, existing_files = self._check_existing_files(video_info)
        missing_indices = [i for i in range(total_pages) if i not in existing_indices]

        if not missing_indices:
            logger.info(f"[BilibiliDownloader] 所有分P已存在，无需下载")
            return self._sort_files_by_page_order(existing_files, video_info)

        # 3. 仅下载缺失的分P（转换为1-based索引范围）
        logger.info(f"[BilibiliDownloader] 需要下载分P：{[i + 1 for i in missing_indices]}")
        p_start = missing_indices[0] + 1
        p_end = missing_indices[-1] + 1
        p_range = (p_start, p_end) if p_start != p_end else (p_start,)

        # 4. 根据分P数量选择下载API
        if total_pages > 1:
            logger.info(f"[BilibiliDownloader] 下载合集缺失分P（{p_start}-{p_end}）")
            await d.get_series(
                url=url,
                path=self.download_path,
                quality=80,
                subtitle=True,
                image=False,
                p_range=p_range  # 仅下载缺失范围
            )
        else:
            logger.info(f"[BilibiliDownloader] 下载单P视频")
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

    # 5. 收集所有文件并按分P顺序排序
    all_files = self._collect_all_video_files()
    return self._sort_files_by_page_order(all_files, video_info)


def _check_existing_files(self, video_info) -> tuple[set[int], list[str]]:
    """检查已存在的视频文件，返回存在的分P索引和文件路径"""
    existing_indices = set()
    existing_files = []
    all_files = self._collect_all_video_files()

    for page_idx, page in enumerate(video_info.pages):
        # 基于分P标题和ID生成特征字符串（适配bilix的命名规则）
        page特征 = f"{video_info.title}_{page.id}_{page.part}"
        # 模糊匹配（允许文件名包含特征字符串即可）
        for file in all_files:
            if page特征 in os.path.basename(file):
                existing_indices.add(page_idx)
                existing_files.append(file)
                break  # 找到匹配文件即停止当前分P的检查

    return existing_indices, existing_files


def _collect_all_video_files(self) -> list[str]:
    """收集下载目录中所有视频文件"""
    video_extensions = (".mp4", ".flv", ".mkv")
    found = []
    for root, _, files in os.walk(self.download_path):
        for f in files:
            if f.lower().endswith(video_extensions):
                found.append(os.path.join(root, f))
    return found


def _sort_files_by_page_order(self, files: list[str], video_info) -> list[str]:
    """根据视频元信息中的分P顺序对文件排序"""
    # 构建分P特征与索引的映射（修正中文变量名为英文）
    page_feature_to_idx = {}
    for page_idx, page in enumerate(video_info.pages):
        page_feature = f"{video_info.title}_{page.id}_{page.part}"  # 中文"特征"改为英文"feature"
        page_feature_to_idx[page_feature] = page_idx

    # 按分P索引排序文件
    def get_page_index(file: str) -> int:
        for feature, idx in page_feature_to_idx.items():
            if feature in os.path.basename(file):
                return idx
        # 未匹配的文件放最后，并添加警告日志
        logger.warning(f"[BilibiliDownloader] 未匹配到分P信息的文件：{file}")
        return int('inf')  # 无穷大确保排在最后

    sorted_files = sorted(files, key=get_page_index)

    if len(sorted_files) != len(video_info.pages):
        logger.warning(
            f"[BilibiliDownloader] 检测到 {len(video_info.pages)} 个分P，但实际找到 {len(sorted_files)} 个文件")

    return sorted_files
