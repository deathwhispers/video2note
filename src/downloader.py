import asyncio
import os
from bilix.sites.bilibili import DownloaderBilibili
from bilix.exception import APIError

# ----------------------------
# 配置区
# ----------------------------
DEFAULT_DOWNLOAD_DIR = "downloads"
COOKIES_PATH = "cookies.json"  # 建议你提前保存好 cookies.json


async def download_bilibili_video(url: str, cookies_path: str = COOKIES_PATH):
    """
    自动下载 B 站视频，选择非会员最高画质。
    如果 cookies 不存在，则匿名下载（清晰度可能更低）。
    """
    # 检查 cookies 文件是否存在
    cookies = cookies_path if os.path.exists(cookies_path) else None
    if cookies:
        print(f"✅ 使用 cookies 登录: {cookies_path}")
    else:
        print("⚠️ 未检测到 cookies.json，将以匿名方式下载。")

    # 下载目录
    os.makedirs(DEFAULT_DOWNLOAD_DIR, exist_ok=True)

    # 初始化下载器
    d = DownloaderBilibili(cookies=cookies)

    try:
        # 自动选择非会员可下载的最高画质
        print(f"🎬 开始下载: {url}")
        await d.get_video(
            url,
            path=DEFAULT_DOWNLOAD_DIR,
            quality=80,  # 80 通常是非会员最高 (720p)
            hierarchy=True,  # 按UP主/标题自动分层
            image=False,     # 不下载封面
            subtitle=False   # 不下载字幕
        )

    except APIError:
        print("❌ Cookies 已过期或无效，将尝试匿名模式重新下载。")
        d = DownloaderBilibili()
        await d.get_video(
            url,
            path=DEFAULT_DOWNLOAD_DIR,
            quality=80,
            hierarchy=True
        )

    finally:
        await d.aclose()

    print("✅ 下载完成！")


def download_video(video_cfg):
    """
    对外暴露的主函数
    video_cfg 示例:
    {
        "url": "https://www.bilibili.com/video/BV1xx411c7XX",
        "cookies_path": "cookies.json"
    }
    """
    url = video_cfg.get("url")
    cookies_path = video_cfg.get("cookies_path", COOKIES_PATH)
    asyncio.run(download_bilibili_video(url, cookies_path))
    return os.path.abspath(DEFAULT_DOWNLOAD_DIR)


if __name__ == "__main__":
    # 测试用例
    test_cfg = {
        "url": "https://www.bilibili.com/video/BV1xx411c7XX",  # 这里换成你的视频链接
        "cookies_path": "cookies.json"
    }
    download_video(test_cfg)
