# src/video2note/summarizer/qwen_summarizer.py

from video2note.summarizer.base import Summarizer
from video2note.types.note import Note, NoteSection
from video2note.core.exceptions import SummarizationError
from video2note.utils.logger import logging

import dashscope

class QwenSummarizer(Summarizer):
    def __init__(self, config):
        super().__init__(config)
        qwen_cfg = config.providers.qwen
        self.api_key = qwen_cfg.api_key
        if not self.api_key:
            raise ValueError("Qwen API key not configured")
        dashscope.api_key = self.api_key

        # 模型 /温度
        self.model = getattr(self.config.ai, "model", "qwen-plus")
        self.temperature = getattr(self.config.ai, "temperature", 0.7)
        self.prompt_template = getattr(qwen_cfg, "prompt_template", "{{transcript}}")

    def summarize(self, text: str, frames: list[str] | None = None) -> Note:
        logging.info(f"[QwenSummarizer] 模型 {self.model} 开始摘要")
        try:
            frames_str = "\n".join(frames) if frames else ""
            prompt = self.prompt_template.replace("{{transcript}}", text).replace("{{frames}}", frames_str)
            response = dashscope.Generation.call(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature
            )
            if response.status_code == dashscope.StatusCode.SUCCESS:
                content = response.output.get("text", "")
                note = Note(
                    title="Qwen 笔记",
                    sections=[NoteSection("内容", content)],
                    metadata={}
                )
                return note
            else:
                raise SummarizationError(f"Qwen summarization failed: {response.message}")
        except Exception as e:
            logging.error(f"[QwenSummarizer] 生成失败: {e}")
            raise SummarizationError(f"Qwen summarization error: {e}")
