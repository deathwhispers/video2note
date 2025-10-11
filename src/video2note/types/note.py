# src/video2note/types/note.py


class NoteSection:
    def __init__(self, title: str, content: str):
        self.title = title
        self.content = content


class Note:
    def __init__(self, title: str, sections: list[NoteSection], metadata: dict = None, frames: list[str] = None):
        self.title = title
        self.sections = sections
        self.metadata = metadata or {}
        self.frames = frames or []

    def to_markdown(self) -> str:
        # 如果有 frames，可把 frames embed 或留给同步模块处理
        md = f"# {self.title}\n\n"
        for sec in self.sections:
            md += f"## {sec.title}\n\n{sec.content}\n\n"
        return md
