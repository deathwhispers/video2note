import requests
import json

def sync_to_notion(summary, config):
    if not config.get("enable", False):
        print("[notion_sync] Notion sync disabled")
        return

    token = config.get("token")
    database_id = config.get("database_id")
    tags = config.get("tags", [])
    status = config.get("publish_status", "Published")

    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    data = {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {"title": [{"text": {"content": f"视频笔记 {status}"}}]},
            "Tags": {"multi_select": [{"name": tag} for tag in tags]},
            "Status": {"select": {"name": status}}
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"text": [{"type": "text", "text": {"content": summary}}]}
            }
        ]
    }

    resp = requests.post(url, headers=headers, data=json.dumps(data))
    if resp.status_code in [200, 201]:
        print("[notion_sync] Notion sync completed")
    else:
        print(f"[notion_sync] Failed: {resp.status_code}, {resp.text}")
