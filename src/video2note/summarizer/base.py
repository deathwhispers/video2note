# src/video2note/summarizer/base.py

import os
from abc import ABC, abstractmethod

from video2note.types.note import Note
from video2note.utils.file_utils import ensure_dir
from video2note.utils.logger import logging


class Summarizer(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def summarize(self, text: str, frames: list[str] | None = None) -> Note:
        """
        用给定的原文 /转写文本 + 可选帧路径列表生成结构化 Note 对象。
        如果失败，抛出 SummarizationError。
        """
        raise NotImplementedError


class SummarizerFactory:
    @staticmethod
    def create(provider: str, config) -> Summarizer:
        prov = provider.lower()
        if prov == "openai":
            from video2note.summarizer.openai_summarizer import OpenAISummarizer
            return OpenAISummarizer(config)
        elif prov == "rule":
            from video2note.summarizer.rule_summarizer import RuleSummarizer
            return RuleSummarizer(config)
        elif prov == "local":
            from video2note.summarizer.local_summarizer import LocalSummarizer
            return LocalSummarizer(config)
        elif prov == "doubao":
            from video2note.summarizer.doubao_summarizer import DoubaoSummarizer
            return DoubaoSummarizer(config)
        elif prov == "qwen":
            from video2note.summarizer.qwen_summarizer import QwenSummarizer
            return QwenSummarizer(config)
        else:
            raise ValueError(f"Unsupported summarizer provider: {provider}")


def save_markdown(md_text: str, output_dir: str, filename: str = "note.md") -> str:
    ensure_dir(output_dir)
    file_path = os.path.join(output_dir, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    logging.info(f"[summarizer] 笔记已保存: {file_path}")
    return file_path
