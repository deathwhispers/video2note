# src/video2note/notion/base.py

from abc import ABC, abstractmethod

from video2note.types.note import Note


class Syncer(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def sync(self, note: Note) -> bool:
        """
        将 Note 对象同步到目标平台（如 Notion）。
        返回 True 表示同步成功，False /抛异常表示失败。
        """
        raise NotImplementedError


class SyncerFactory:
    @staticmethod
    def create(provider: str, config) -> Syncer:
        provider = provider.lower()
        if provider == "notion":
            from video2note.notion.sync_notion import NotionSyncer
            return NotionSyncer(config)
        else:
            raise ValueError(f"Unsupported sync provider: {provider}")
