import asyncio
import os
from pathlib import Path

import bilix.sites.bilibili.api
from bilix.exception import APIError, APIResourceError, APIUnsupportedError
from bilix.sites.bilibili import DownloaderBilibili

from utils import ensure_dir, logger


async def download_bilibili_video(url: str, download_path: str):
    """
    下载B站视频（自动区分单P/合集，调用对应API）
    :param url: 视频URL（单P或合集）
    :param download_path: 保存根目录
    """
    # 初始化下载器（匿名模式）
    d = DownloaderBilibili()
    download_path = Path(download_path)
    ensure_dir(download_path)

    try:
        # 1. 先获取视频基础信息，判断是单P还是合集
        logger.info(f"[downloader] 解析视频信息：{url}")
        video_info = await bilix.sites.bilibili.api.get_video_info(d.client, url)

        # 2. 根据分P数量选择API：pages长度>1则为合集，调用get_series；否则调用get_video
        if len(video_info.pages) > 1:
            logger.info(f"[downloader] 检测到合集（共 {len(video_info.pages)} 分P），使用get_series下载")
            # 调用合集下载API（支持分P范围、字幕等参数）
            await d.get_series(
                url=url,
                path=download_path,
                quality=80,  # 720p（非会员可用）
                subtitle=True,  # 下载字幕
                image=False,  # 不下载封面
                p_range=None  # 下载全部分P（如需指定范围可传(1,3)下载P1-P3）
            )
        else:
            logger.info(f"[downloader] 检测到单P视频，使用get_video下载")
            # 调用单视频下载API
            await d.get_video(
                url=url,
                path=download_path,
                quality=80,
                subtitle=True,
                image=False
            )

        logger.info(f"[downloader] 下载完成，保存至：{download_path}")

    except (APIResourceError, APIUnsupportedError) as e:
        logger.error(f"[downloader] 资源错误（视频可能不存在或不支持）：{str(e)}")
        raise
    except APIError as e:
        logger.error(f"[downloader] API调用失败：{str(e)}")
        raise
    except Exception as e:
        logger.error(f"[downloader] 下载异常：{str(e)}")
        raise
    finally:
        await d.aclose()  # 关闭下载器


def download_video(video_url: str, download_path: str) -> list:
    """
    对外接口：下载视频（支持单P/合集），返回有序视频文件列表
    :param video_url: 视频URL
    :param download_path: 保存目录
    :return: 视频文件路径列表（按分P顺序）
    """
    # 执行异步下载
    asyncio.run(download_bilibili_video(url=video_url, download_path=download_path))

    # 收集所有视频文件（按创建时间排序，确保分P顺序）
    video_extensions = (".mp4", ".flv", ".mkv")
    video_files = []
    for root, _, files in os.walk(download_path):
        for file in files:
            if file.lower().endswith(video_extensions):
                video_path = os.path.join(root, file)
                video_files.append(video_path)

    # 按文件创建时间排序（先下载的分P排在前）
    video_files.sort(key=lambda x: os.path.getctime(x))

    if not video_files:
        raise FileNotFoundError(f"在 {download_path} 中未找到视频文件")

    logger.info(f"[downloader] 共发现 {len(video_files)} 个视频文件（按分P顺序）")
    return video_files
