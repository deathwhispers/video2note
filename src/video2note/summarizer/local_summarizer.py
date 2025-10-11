# src/video2note/summarizer/local_summarizer.py

from video2note.summarizer.base import Summarizer
from video2note.types.note import Note, NoteSection
from video2note.core.exceptions import SummarizationError
from video2note.utils.logger import logging

class LocalSummarizer(Summarizer):
    def summarize(self, text: str, frames: list[str] | None = None) -> Note:
        try:
            local_cfg = self.config.providers.local
            method = getattr(local_cfg, "summarizer", "rule").lower()

            if method == "rule":
                # 复用 RuleSummarizer 的逻辑
                from video2note.summarizer.rule_summarizer import RuleSummarizer
                return RuleSummarizer(self.config).summarize(text, frames)
            elif method == "light-nlp":
                # 你的轻量 NLP 版本逻辑
                # 例如用 spaCy /nltk 等
                import spacy
                from nltk.tokenize import sent_tokenize
                nlp = spacy.load("zh_core_web_sm")
                doc = nlp(text[:5000])
                keywords = [ent.text for ent in doc.ents if ent.label_ in ("PERSON", "ORG", "GPE", "PRODUCT")]
                sentences = sent_tokenize(text)
                chunks = [sentences[i:i+5] for i in range(0, len(sentences), 5)]

                sections: list[NoteSection] = []
                title = "视频笔记（关键词：" + ", ".join(keywords[:5]) + "）"
                sections.append(NoteSection("核心内容", "\n".join([" ".join(chunk) for chunk in chunks[:3]])))
                if frames:
                    mdf = "\n".join(f"![帧{i}]({f})" for i, f in enumerate(frames[:3]))
                    sections.append(NoteSection("关键帧", mdf))
                return Note(title=title, sections=sections, metadata={})
            else:
                logging.warning(f"[LocalSummarizer] 未知 local summarizer 方法 {method}，回退 rule")
                from video2note.summarizer.rule_summarizer import RuleSummarizer
                return RuleSummarizer(self.config).summarize(text, frames)
        except Exception as e:
            logging.error(f"[LocalSummarizer] 本地摘要失败: {e}")
            raise SummarizationError(f"Local summarizer failed: {e}")
