# src/video2note/summarizer/doubao_summarizer.py

from video2note.summarizer.base import Summarizer
from video2note.types.note import Note, NoteSection
from video2note.core.exceptions import SummarizationError
from video2note.utils.logger import logging

import requests

class DoubaoSummarizer(Summarizer):
    def summarize(self, text: str, frames: list[str] | None = None) -> Note:
        doubao_cfg = self.config.providers.doubao
        api_key = doubao_cfg.api_key
        endpoint = getattr(doubao_cfg, "endpoint", "https://api.doubao.com/v1/chat/completions")
        if not api_key:
            raise ValueError("Doubao API key not configured")

        model = getattr(self.config.ai, "model", "doubao-pro")
        temperature = getattr(self.config.ai, "temperature", 0.7)
        prompt_template = getattr(doubao_cfg, "prompt_template", "{{transcript}}")

        frames_str = "\n".join(frames) if frames else ""
        prompt = prompt_template.replace("{{transcript}}", text).replace("{{frames}}", frames_str)

        logging.info(f"[DoubaoSummarizer] 使用模型 {model} 生成笔记")
        try:
            resp = requests.post(
                url=endpoint,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature
                },
                timeout=60
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            note = Note(
                title="豆包笔记",
                sections=[NoteSection("内容", content)],
                metadata={}
            )
            return note
        except Exception as e:
            logging.error(f"[DoubaoSummarizer] 生成失败: {e}")
            raise SummarizationError(f"Doubao summarization failed: {e}")
