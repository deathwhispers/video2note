import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, Optional

from src.utils import load_config, ensure_dir

# -------------------------------
# 初始化日志
# -------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# -------------------------------
# 可选依赖
# -------------------------------
try:
    from bilix.sites.bilibili import DownloaderBilibili
except ImportError as e:
    raise ImportError("请先安装 bilix >= 0.18.0: pip install -U bilix") from e

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


class VideoDownloader:
    """通用视频下载器，支持 Bilibili / YouTube / Mock 模式"""

    def __init__(self, config: Dict):
        self.config = config
        self.video_cfg = config.get("video", {})
        self.app_cfg = config.get("app", {})

        self.source = self.video_cfg.get("source")
        self.output_dir = ensure_dir(self.video_cfg.get("download_path", "./downloads"))
        self.language = self.video_cfg.get("language", "zh")
        self.quality = self.video_cfg.get("quality", "best")
        self.login_cfg = self.video_cfg.get("login", {})

        self.mock = bool(self.app_cfg.get("mock", False))  # 从 app 读取 mock

        if not self.source:
            raise ValueError("config.video.source 未配置视频地址")

        # 自动识别平台
        if "bilibili.com" in self.source:
            self.platform = "bilibili"
        elif "youtube.com" in self.source or "youtu.be" in self.source:
            self.platform = "youtube"
        else:
            self.platform = "unknown"

    async def download(self):
        """主入口：根据平台分发下载逻辑"""
        if self.mock:
            logger.warning("[MOCK] 模拟下载模式已启用，不会下载真实视频。")
            fake_path = os.path.join(self.output_dir, "mock_video.mp4")
            with open(fake_path, "w", encoding="utf-8") as f:
                f.write("This is a mock video file.")
            logger.info(f"[MOCK] 模拟视频已生成: {fake_path}")
            return [fake_path]

        if self.platform == "bilibili":
            return await self._download_bilibili()
        elif self.platform == "youtube":
            return self._download_youtube()
        else:
            raise ValueError(f"不支持的平台: {self.source}")

    async def _download_bilibili(self):
        """B站下载逻辑"""
        login_method = self.login_cfg.get("method", "qrcode")
        username = self.login_cfg.get("username")
        password = self.login_cfg.get("password")

        cookie_path = Path("cookies") / "bilibili.txt"
        cookie_path.parent.mkdir(parents=True, exist_ok=True)

        dl = DownloaderBilibili(cookie_file=str(cookie_path))

        if not cookie_path.exists():
            if login_method == "account" and username and password:
                logger.info("[Bilibili] 使用账号密码登录 ...")
                await dl.login_by_password(username, password)
                await dl.save_cookies(str(cookie_path))
            elif login_method == "qrcode":
                logger.info("[Bilibili] 使用扫码登录 ...")
                await dl.login_by_qrcode()
                await dl.save_cookies(str(cookie_path))
            else:
                raise ValueError(f"[Bilibili] 未知的登录方式: {login_method}")
        else:
            logger.info("[Bilibili] 检测到已存在 cookies，将直接使用。")

        logger.info(f"[Bilibili] 开始下载视频: {self.source}")
        await dl.get_video(self.source, path=self.output_dir, quality=self.quality)
        logger.info(f"[Bilibili] 视频已下载到: {self.output_dir}")
        return [self.output_dir]

    def _download_youtube(self):
        """YouTube 下载逻辑"""
        if not yt_dlp:
            raise ImportError("请先安装 yt-dlp: pip install -U yt-dlp")

        ydl_opts = {
            "outtmpl": os.path.join(self.output_dir, "%(title)s.%(ext)s"),
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "quiet": False,
        }

        logger.info(f"[YouTube] 开始下载视频: {self.source}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.source])
        logger.info(f"[YouTube] 视频已下载到: {self.output_dir}")
        return [self.output_dir]


# -------------------------------
# CLI 入口
# -------------------------------
async def download_video(config_path: str = "config.yaml"):
    config = load_config(config_path)
    downloader = VideoDownloader(config)
    await downloader.download()


if __name__ == "__main__":
    asyncio.run(download_video())
