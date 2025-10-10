import os

from dotenv import load_dotenv

from src.downloader import download_video  # 注意：需确保download_video返回视频文件列表
from src.notion_sync import sync_to_notion
from src.summarizer import summarize, save_markdown
from src.transcriber import extract_audio, transcribe, extract_key_frames
from src.utils import load_config, logger, parse_subtitles

# 加载 .env 文件（如果存在）
load_dotenv()


def run_pipeline():
    # 加载配置文件
    cfg = load_config()
    video_cfg = cfg.get("video", {})
    output_cfg = cfg.get("output", {})

    # 基础配置提取
    download_path = video_cfg.get("download_path", "./downloads")
    frame_interval = video_cfg.get("frame_interval", 100)  # 关键帧提取间隔（秒）
    markdown_path = output_cfg.get("markdown_path", "./notes")

    # 1. 下载视频（支持合集，返回视频文件列表）
    logger.info("===== Step 1: 下载视频 =====")
    video_url = video_cfg.get("url")
    if not video_url:
        logger.error("配置中未设置视频URL（video.url），终止流程")
        return

    try:
        # 下载视频（返回所有视频文件路径的列表，支持合集）
        video_files = download_video(video_url, download_path)  # 传入下载路径，确保合集文件保存在统一目录
        if not video_files or not all(os.path.exists(f) for f in video_files):
            logger.error("视频下载不完整，终止流程")
            return
        logger.info(f"[main] 视频下载完成，共 {len(video_files)} 个文件：{video_files}")
    except Exception as e:
        logger.error(f"视频下载失败：{str(e)}", exc_info=True)
        return

    # 2. 解析所有字幕（支持多视频字幕合并）
    logger.info("===== Step 2: 解析字幕 =====")
    subtitles = parse_subtitles(download_path)  # 解析整个下载目录下的字幕
    subtitle_text = ""
    if subtitles:
        # 按字幕文件顺序合并内容（可根据文件名排序，确保与视频顺序一致）
        sorted_subtitles = sorted(subtitles, key=lambda x: x["path"])  # 按路径排序
        subtitle_text = "\n\n".join(
            [f"【字幕文件：{s['path'].split('/')[-1]}】\n{s['content']}" for s in sorted_subtitles])
    else:
        logger.warning("未找到字幕文件，将仅使用音频转写内容")

    # 3. 音频转写（循环处理每个视频）
    logger.info("===== Step 3: 音频转写 =====")
    transcript_texts = []
    for i, video_file in enumerate(video_files, 1):
        logger.info(f"[转写] 处理第 {i}/{len(video_files)} 个视频：{video_file}")
        # 提取音频（保存到下载目录下的audios子目录，避免文件冲突）
        audio_dir = os.path.join(download_path, "audios")
        audio_file = extract_audio(video_file, audio_dir)
        if not audio_file:
            logger.warning(f"第 {i} 个视频音频提取失败，跳过转写")
            continue

        # 调用AI转写
        audio_transcript = transcribe(audio_file, cfg)
        transcript_texts.append(f"【视频 {i} 音频转写】\n{audio_transcript}")

    if not transcript_texts:
        logger.error("所有视频音频转写失败，终止流程")
        return

    # 4. 提取关键帧（循环处理每个视频）
    logger.info("===== Step 4: 提取关键帧 =====")
    all_frames = []
    frame_dir = os.path.join(download_path, "images")  # 所有视频的帧保存在统一目录
    for i, video_file in enumerate(video_files, 1):
        logger.info(f"[帧提取] 处理第 {i}/{len(video_files)} 个视频：{video_file}")
        # 为每个视频创建子目录保存帧，避免文件名冲突（如 frame_0001.jpg 重复）
        video_frame_dir = os.path.join(frame_dir, f"video_{i}")
        frames = extract_key_frames(video_file, video_frame_dir, interval=frame_interval)
        all_frames.extend(frames)

    logger.info(f"共提取关键帧 {len(all_frames)} 张")

    # 5. 合并转写与字幕内容，生成完整文本
    full_transcript = f"【所有字幕内容汇总】\n{subtitle_text}\n\n【所有音频转写汇总】\n{''.join(transcript_texts)}"

    # 6. 生成Markdown笔记
    logger.info("===== Step 5: 生成Markdown =====")
    try:
        md_text = summarize(full_transcript, cfg, frames=all_frames)
        # 生成带视频标题的文件名（从URL提取或用默认名）
        video_title = video_url.split("/")[-1].strip() or "video_note"
        md_filename = f"{video_title}.md"
        md_file = save_markdown(md_text, markdown_path, filename=md_filename)
    except Exception as e:
        logger.error(f"笔记生成失败：{str(e)}", exc_info=True)
        return

    # 7. 同步到Notion（可选）
    if cfg.get("notion", {}).get("enable", True):
        logger.info("===== Step 6: 同步到Notion =====")
        try:
            sync_to_notion(md_file, cfg, frames=all_frames)
        except Exception as e:
            logger.error(f"Notion同步失败：{str(e)}", exc_info=True)  # 同步失败不中断整个流程

    logger.info("===== 全流程完成 =====")


if __name__ == "__main__":
    run_pipeline()
