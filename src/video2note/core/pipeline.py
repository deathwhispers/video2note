# src/video2note/core/pipeline.py
import logging
from pathlib import Path
from typing import Optional, List

from video2note.summarizer.base import SummarizerFactory
from video2note.transcriber.base import TranscriberFactory, Transcriber
from video2note.transcriber.base import extract_audio
from video2note.types.note import Note
from video2note.types.transcript import Transcript
from video2note.types.video import DownloadedVideo


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
    """
    TranscribeStage 支持两种使用模式：
    1) pipeline 模式：ctx 中包含 "video"（DownloadedVideo），则对 video.meta['all_video_paths'] 中每个视频抽取音频并转写
    2) debug 模式：在构造的时候传入 input_paths（list[str]），则直接对这些路径转写（便于单元/调试）
    """

    def __init__(self, config, input_paths: Optional[List[str]] = None):
        super().__init__(config)
        self.input_paths = input_paths

    def run(self, ctx: dict):

        provider = self.config.transcriber.provider if hasattr(self.config, "transcriber") else getattr(self.config.ai,
                                                                                                        "provider",
                                                                                                        "local")
        transcriber: Transcriber = TranscriberFactory.create(provider, self.config)

        targets: List[str] = []
        # 优先使用 input_paths（单独调试）
        if self.input_paths:
            targets = list(self.input_paths)
        else:
            video_obj: DownloadedVideo = ctx.get("video")
            if not video_obj:
                raise RuntimeError("TranscribeStage: no video in ctx and no input_paths provided")
            targets = video_obj.meta.get("all_video_paths", [])  # list of video file paths

        transcripts: List[Transcript] = []
        # 临时音频目录放在 downloads/<video_id>/audios/
        project_root = Path(__file__).resolve().parents[2]
        audio_tmp_root = (project_root / (getattr(self.config.video, "download_path", "downloads"))) / "tmp_audios"
        audio_tmp_root = audio_tmp_root.resolve()
        audio_tmp_root.mkdir(parents=True, exist_ok=True)

        for vp in targets:
            # 如果 vp 本身是音频文件（.wav/.mp3），直接传入；否则先抽音
            p = Path(vp)
            if p.suffix.lower() in (".wav", ".mp3", ".m4a"):
                audio_path = str(p)
            else:
                audio_path = extract_audio(str(p), str(audio_tmp_root))
                if audio_path is None:
                    raise RuntimeError(f"Failed to extract audio from {vp}")
            # 转写单个音频
            transcript = transcriber.transcribe(audio_path)
            transcripts.append(transcript)

        ctx["transcripts"] = transcripts
        logging.info(f"[TranscribeStage] produced {len(transcripts)} transcripts")


class SummarizeStage(Stage):
    """
    对每个 transcript 生成单独笔记（每个分P一篇）。
    输出保存到 config.output.markdown_path（相对项目根或绝对路径）。
    结果放到 ctx['notes'] 列表，元素为 dict {'note': Note, 'md_path': str}
    """

    def run(self, ctx: dict):
        summarizer_provider = getattr(self.config, "summarizer", None)
        if summarizer_provider is None:
            # 兼容早期 config 结构
            summarizer_provider = getattr(self.config.ai, "provider", None) or getattr(self.config, "ai", {}).get(
                "provider", "openai")
        # create summarizer
        summarizer = SummarizerFactory.create(
            summarizer_provider.provider if hasattr(summarizer_provider, "provider") else (
                summarizer_provider if isinstance(summarizer_provider, str) else getattr(self.config, "ai").provider),
            self.config)  # handle a few config shapes
        # But above line is a bit defensive; simpler:
        try:
            summarizer = SummarizerFactory.create(self.config.ai.provider, self.config)
        except Exception:
            summarizer = SummarizerFactory.create(getattr(self.config, "summarizer", "rule"), self.config)

        transcripts: List[Transcript] = ctx.get("transcripts", [])
        if not transcripts:
            raise RuntimeError("SummarizeStage: no transcripts in ctx")

        # output dir
        project_root = Path(__file__).resolve().parents[2]
        md_output = Path(getattr(self.config.output, "markdown_path", "notes"))
        if not md_output.is_absolute():
            md_output = (project_root / md_output).resolve()
        md_output.mkdir(parents=True, exist_ok=True)

        notes = []
        # try to get associated video paths (if available)
        video_paths = []
        video_obj = ctx.get("video")
        if video_obj:
            video_paths = video_obj.meta.get("all_video_paths", [])

        for idx, transcript in enumerate(transcripts):
            text = transcript.get_full_text()
            # call summarizer
            note_obj: Note = summarizer.summarize(text, frames=None)
            # build title per-video (prefer video file name)
            if idx < len(video_paths):
                vp = Path(video_paths[idx])
                title_base = vp.stem
            else:
                title_base = f"video_part_{idx + 1}"
            # set title
            note_obj.title = title_base
            # save markdown
            md_text = note_obj.to_markdown()
            filename = f"{title_base}.md"
            md_path = str((md_output / filename).resolve())
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_text)
            notes.append({"note": note_obj, "md_path": md_path})
            logging.info(f"[SummarizeStage] wrote note: {md_path}")

        ctx["notes"] = notes


class SyncStage(Stage):
    def run(self, ctx: dict):
        from video2note.notion.base import SyncerFactory

        note = ctx.get("note")
        if note is None:
            raise RuntimeError("No note object in context")

        syncer = SyncerFactory.create(self.config.notion.provider, self.config)
        success = syncer.sync(note)
        ctx["sync_success"] = success
