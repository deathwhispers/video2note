# src/video2note/notion/notion_client.py

from notion_client import Client
from video2note.notion.base import Syncer
from video2note.types.note import Note
from video2note.core.exceptions import SyncError
from video2note.utils.logger import logging
from video2note.notion.md_parser import markdown_to_notion_blocks

class NotionSyncer(Syncer):
    def __init__(self, config):
        super().__init__(config)
        notion_cfg = config.notion
        self.token = notion_cfg.token
        self.database_id = notion_cfg.database_id
        if not self.token or not self.database_id:
            raise ValueError("Notion token or database_id must be configured")
        self.client = Client(auth=self.token)

    def sync(self, note: Note) -> bool:
        """
        同步 Note 对象到 Notion。
        """
        try:
            title = note.title
            md_text = note.to_markdown()
            blocks = markdown_to_notion_blocks(md_text, note.frames)

            # 查询是否已有该页面
            query_res = self.client.databases.query(
                database_id=self.database_id,
                filter={"property": "Name", "title": {"equals": title}}
            )
            existing = query_res.get("results", [])

            if existing:
                page_id = existing[0]["id"]
                logging.info(f"[NotionSyncer] 更新页面: {title} (page_id={page_id})")
                self.client.pages.update(
                    page_id=page_id,
                    properties={"Name": {"title": [{"text": {"content": title}}]}},
                    children=blocks
                )
            else:
                logging.info(f"[NotionSyncer] 创建页面: {title}")
                self.client.pages.create(
                    parent={"database_id": self.database_id},
                    properties={"Name": {"title": [{"text": {"content": title}}]}},
                    children=blocks
                )
            return True
        except Exception as e:
            logging.error(f"[NotionSyncer] 同步失败: {e}")
            raise SyncError(f"Notion sync failed: {e}")
