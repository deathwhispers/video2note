# src/video2note/core/pipeline.py

class Stage:
    def __init__(self, config):
        self.config = config

    def run(self, ctx: dict):
        raise NotImplementedError


class DownloadStage(Stage):
    def run(self, ctx: dict):
        from video2note.downloader.base import DownloaderFactory
        video_provider = self.config.video.provider
        downloader = DownloaderFactory.create(video_provider, self.config)
        url = self.config.video.url
        video_obj = downloader.download(url)
        ctx["video"] = video_obj


class TranscribeStage(Stage):
    def run(self, ctx: dict):
        from video2note.transcriber.base import TranscriberFactory
        from video2note.transcriber.base import extract_audio

        video = ctx.get("video")
        if not video:
            raise RuntimeError("video not present in context")

        # 假设你已经在 downloader 阶段获取视频文件列表存储在 video_obj.frame_paths
        video_files = video.frame_paths  # 假设是 List[str]

        transcripts = []
        for vf in video_files:
            # 提取音频
            audio_path = extract_audio(vf, self.config)
            transcriber = TranscriberFactory.create(self.config.transcriber.provider, self.config)
            transcript = transcriber.transcribe(audio_path)
            transcripts.append(transcript)

        ctx["transcripts"] = transcripts


class SummarizeStage(Stage):
    def run(self, ctx: dict):
        from video2note.summarizer.base import SummarizerFactory
        from video2note.summarizer.base import save_markdown
        transcripts = ctx.get("transcripts")
        if not transcripts:
            raise RuntimeError("transcripts not present in context")

        # 将多个 Transcript 对象合并为一个文本（策略可自定义）
        full_texts = [t.get_full_text() for t in transcripts]
        merged_text = "\n\n".join(full_texts)

        # 获取帧路径（如果你在下载阶段 /transcriber阶段也提取帧的话）
        frames = ctx.get("frames")  # 有可能为空或者列表[str]

        summarizer = SummarizerFactory.create(self.config.summarizer.provider, self.config)
        note = summarizer.summarize(merged_text, frames)
        ctx["note"] = note

        # 保存成 Markdown（如果你希望 pipeline 负责保存）

        output_dir = self.config.output.markdown_path  # 假定你在配置里有这项
        md_text = note.to_markdown()
        md_path = save_markdown(md_text, output_dir)
        ctx["note_path"] = md_path


class SyncStage(Stage):
    def run(self, ctx: dict):
        from video2note.notion.base import SyncerFactory

        note = ctx.get("note")
        if note is None:
            raise RuntimeError("No note object in context")

        syncer = SyncerFactory.create(self.config.notion.provider, self.config)
        success = syncer.sync(note)
        ctx["sync_success"] = success
