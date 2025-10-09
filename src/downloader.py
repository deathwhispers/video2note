import os
import subprocess
import re
from utils import ensure_dir, load_yaml_config


# ------------------------------------------
# 下载器映射表（可根据需要扩展）
# ------------------------------------------
DOWNLOADER_MAP = {
    "youtube": {
        "patterns": [r"youtube\.com", r"youtu\.be"],
        "cmd": ["yt-dlp", "-f", "best", "-o", "{output}", "{url}"],
    },
    "bilibili": {
        "patterns": [r"bilibili\.com"],
        "cmd": ["you-get", "-o", "{output_dir}", "{url}"],
    },
    "tencent": {
        "patterns": [r"v\.qq\.com"],
        "cmd": ["you-get", "-o", "{output_dir}", "{url}"],
    },
    "douyin": {
        "patterns": [r"douyin\.com"],
        "cmd": ["yt-dlp", "-o", "{output}", "{url}"],
    },
    "weibo": {
        "patterns": [r"weibo\.com"],
        "cmd": ["you-get", "-o", "{output_dir}", "{url}"],
    },
}


# ------------------------------------------
# 自动识别视频来源
# ------------------------------------------
def detect_provider(url: str) -> str:
    for provider, cfg in DOWNLOADER_MAP.items():
        for pattern in cfg["patterns"]:
            if re.search(pattern, url):
                return provider
    return "unknown"


# ------------------------------------------
# 核心下载函数
# ------------------------------------------
def download_video(url, download_path, tag=None, config_path="config/config.yaml"):
    ensure_dir(download_path)
    config = load_yaml_config(config_path)
    download_cfg = config.get("download", {})

    mock_enabled = download_cfg.get("mock", False)
    proxy = download_cfg.get("proxy", None)
    timeout = download_cfg.get("timeout", 600)
    fallback_to_mock = download_cfg.get("fallback_to_mock", True)

    provider = tag or detect_provider(url)
    provider_cfg = DOWNLOADER_MAP.get(provider)
    filename = os.path.join(download_path, f"{provider}_video.mp4")

    print(f"[downloader] Detected provider: {provider}")
    print(f"[downloader] Download target: {filename}")

    # 如果开启 mock 模式
    if mock_enabled:
        print("[downloader] Mock mode enabled in config, creating mock file.")
        return mock_download(filename)

    if provider_cfg is None:
        print(f"[downloader] No matching provider for URL: {url}")
        if fallback_to_mock:
            print("[downloader] Fallback to mock mode.")
            return mock_download(filename)
        raise RuntimeError("Unsupported video source and mock disabled.")

    # 构造下载命令
    cmd_template = provider_cfg["cmd"]
    cmd = [arg.format(url=url, output=filename, output_dir=download_path) for arg in cmd_template]

    # 添加代理支持
    if proxy and "yt-dlp" in cmd[0]:
        cmd.insert(1, f"--proxy={proxy}")

    print(f"[downloader] Executing: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True, timeout=timeout)
        print(f"[downloader] Download complete: {filename}")
        return filename
    except subprocess.TimeoutExpired:
        print(f"[downloader] Timeout after {timeout} seconds.")
    except subprocess.CalledProcessError as e:
        print(f"[downloader] Command failed: {e}")
    except FileNotFoundError:
        print("[downloader] Downloader tool not found, please install yt-dlp or you-get.")

    # 自动回退
    if fallback_to_mock:
        print("[downloader] Falling back to mock mode due to failure.")
        return mock_download(filename)
    else:
        raise RuntimeError(f"Download failed for {url} and mock fallback disabled.")


# ------------------------------------------
# 模拟下载（离线模式）
# ------------------------------------------
def mock_download(filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("This is a mock video file for testing only.\n")
    print(f"[downloader] Mock video created at: {filename}")
    return filename


# ------------------------------------------
# 测试运行入口
# ------------------------------------------
if __name__ == "__main__":
    test_urls = [
        "https://www.youtube.com/watch?v=abcd1234",
        "https://www.bilibili.com/video/BV1xx411c7mD",
        "https://v.qq.com/x/page/x12345.html",
        "https://www.douyin.com/video/123456",
        "https://weibo.com/xxxxxx"
    ]

    for url in test_urls:
        try:
            download_video(url, "downloads/")
        except Exception as e:
            print(f"[downloader] Error: {e}")
