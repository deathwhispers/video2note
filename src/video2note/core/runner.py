# src/video2note/core/runner.py

from video2note.core.pipeline import (
    DownloadStage, TranscribeStage, SummarizeStage, SyncStage
)
from video2note.core.exceptions import Video2NoteError


class Runner:
    def __init__(self, config):
        self.config = config

    def run_full(self):
        ctx = {}
        stages = [
            DownloadStage(self.config),
            TranscribeStage(self.config),
            SummarizeStage(self.config),
            SyncStage(self.config),
        ]
        for stage in stages:
            try:
                stage.run(ctx)
            except Video2NoteError as e:
                # 统一捕获流程级错误
                # 你可以在这里做日志 /回滚 /通知等
                raise

    def run_download_only(self):
        ctx = {}
        DownloadStage(self.config).run(ctx)

    def run_transcribe_only(self):
        ctx = {}
        # 假设 note 已经生成 / 从本地加载
        TranscribeStage(self.config).run(ctx)

    def run_summarize_only(self):
        ctx = {}
        SummarizeStage(self.config).run(ctx)

    def run_sync_only(self):
        ctx = {}
        # 假设 note 已经生成 / 从本地加载
        SyncStage(self.config).run(ctx)
