# src/video2note/summarizer/rule_summarizer.py

from video2note.core.exceptions import SummarizationError
from video2note.summarizer.base import Summarizer
from video2note.types.note import Note, NoteSection
from video2note.utils.logger import logging


class RuleSummarizer(Summarizer):
    def summarize(self, text: str, frames: list[str] | None = None) -> Note:
        try:
            # 标题部分
            # 假设 config.video.source 是视频源 URL /文件名
            title = str(self.config.video.source).split("/")[-1]

            sections: list[NoteSection] = []

            # 概述：取前300字
            overview = text[:300] + "..."
            sections.append(NoteSection("概述", overview))

            # 如果原文中包含“[字幕内容]”等标记
            if "[字幕内容]" in text:
                seg = text.split("[字幕内容]")[1].split("[音频转写]")[0].strip()
                sections.append(NoteSection("字幕内容", seg))

            if "[音频转写]" in text:
                seg2 = text.split("[音频转写]")[1].strip()
                sections.append(NoteSection("音频转写", seg2))

            # 关键帧引用
            if frames:
                md_lines = []
                for i, frame in enumerate(frames[:5]):
                    md_lines.append(f"![关键帧{i + 1}]({frame})")
                sections.append(NoteSection("关键帧", "\n".join(md_lines)))

            note = Note(title=title, sections=sections, metadata={})
            return note
        except Exception as e:
            logging.error(f"[RuleSummarizer] 生成规则笔记失败: {e}")
            raise SummarizationError(f"Rule summarizer failed: {e}")
