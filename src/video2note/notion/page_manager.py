# src/video2note/notion/page_manager.py

class PageManager:
    def __init__(self, client, database_id):
        self.client = client
        self.database_id = database_id

    def find_page(self, title: str):
        res = self.client.databases.query(
            database_id=self.database_id,
            filter={"property": "Name", "title": {"equals": title}}
        )
        return res.get("results", [])

    def create_page(self, title: str, blocks: list[dict]):
        return self.client.pages.create(
            parent={"database_id": self.database_id},
            properties={"Name": {"title": [{"text": {"content": title}}]}},
            children=blocks
        )

    def update_page(self, page_id: str, title: str, blocks: list[dict]):
        return self.client.pages.update(
            page_id=page_id,
            properties={"Name": {"title": [{"text": {"content": title}}]}},
            children=blocks
        )
