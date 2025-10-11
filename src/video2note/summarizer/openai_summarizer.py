# src/video2note/summarizer/openai_summarizer.py

from video2note.summarizer.base import Summarizer
from video2note.types.note import Note, NoteSection
from video2note.core.exceptions import SummarizationError
from video2note.utils.logger import logging

import openai

class OpenAISummarizer(Summarizer):
    def __init__(self, config):
        super().__init__(config)
        openai_cfg = config.providers.openai
        self.api_key = openai_cfg.api_key
        if not self.api_key:
            raise ValueError("OpenAI API key not set")
        openai.api_key = self.api_key

        self.model = openai_cfg.model
        self.temperature = getattr(openai_cfg, "temperature", 0.7)
        self.prompt_template = openai_cfg.prompt_template

    def summarize(self, text: str, frames: list[str] | None = None) -> Note:
        logging.info(f"[OpenAISummarizer] 调用 OpenAI 模型 {self.model}")
        try:
            frames_str = "\n".join(frames) if frames else ""
            prompt = self.prompt_template.replace("{{transcript}}", text).replace("{{frames}}", frames_str)
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature
            )
            content = response.choices[0].message.content

            # 你可以在返回的 content 里定义约定（例如分章节 / 标题 /内容），这里简单封为一个 section
            note = Note(
                title="笔记",
                sections=[NoteSection("内容", content)],
                metadata={}
            )
            return note
        except Exception as e:
            logging.error(f"[OpenAISummarizer] 生成失败: {e}")
            raise SummarizationError(f"OpenAI summarization failed: {e}")
