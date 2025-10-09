import os
from src.utils import load_config, logger, ensure_dir
from src.downloader import download_video
from src.transcriber import extract_audio, transcribe
from src.summarizer import summarize, save_markdown
from src.notion_sync import sync_to_notion

# -------------------------------
# 主流程
# -------------------------------
def run_pipeline():
    cfg = load_config()
    app_mock = cfg.get("app.mock", False)

    video_cfg = cfg.get("video", {})
    output_cfg = cfg.get("output", {})

    # -------------------------------
    # 1️⃣ 下载视频
    # -------------------------------
    logger.info("===== Step 1: 下载视频 =====")
    download_path = video_cfg.get("download_path", "./downloads")
    video_files = download_video(
        url=video_cfg.get("source"),
        download_path=download_path,
        cookies_path=video_cfg.get("cookies_path"),
        quality=video_cfg.get("quality", "best"),
        mock=app_mock
    )

    # -------------------------------
    # 2️⃣ 转写音频
    # -------------------------------
    logger.info("===== Step 2: 转写音频 =====")
    transcript_texts = []
    for video_file in video_files:
        audio_file = extract_audio(video_file, download_path)
        if audio_file:
            transcript = transcribe(audio_file, cfg)
            transcript_texts.append(transcript)

    # 合并转写结果
    full_transcript = "\n".join(transcript_texts)

    # -------------------------------
    # 3️⃣ 生成 Markdown 技术笔记
    # -------------------------------
    logger.info("===== Step 3: 生成 Markdown 笔记 =====")
    md_text = summarize(full_transcript, cfg)
    markdown_path = output_cfg.get("markdown_path", "./notes")
    ensure_dir(markdown_path)
    md_file = save_markdown(md_text, markdown_path)

    # -------------------------------
    # 4️⃣ 同步到 Notion
    # -------------------------------
    if cfg.get("notion.enable", True):
        logger.info("===== Step 4: 同步到 Notion =====")
        sync_to_notion(md_file, cfg)

    logger.info("===== Pipeline 完成 =====")


# -------------------------------
# CLI
# -------------------------------
if __name__ == "__main__":
    run_pipeline()
