from video2note.summarizer.base import Summarizer
from video2note.types.note import Note

class DeepSeekSummarizer(Summarizer):
    def __init__(self, config):
        super().__init__(config)
        # 你原来的摘要 prompt / openai 参数等

    def summarize(self, transcript) -> Note:
        # 用 transcript.get_full_text() 或分段调用 LLM
        # 输出 Note 对象
        raise NotImplementedError
