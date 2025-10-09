import os
from src.utils import ensure_dir, load_config, logger

# -------------------------------
# 可选依赖 notion-client
# -------------------------------
try:
    from notion_client import Client
except ImportError:
    logger.warning("未安装 notion-client，自动安装中...")
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "notion-client"])
    from notion_client import Client


# -------------------------------
# 读取 Markdown 文件内容
# -------------------------------
def read_markdown(md_path):
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Markdown 文件不存在: {md_path}")
    with open(md_path, "r", encoding="utf-8") as f:
        return f.read()


# -------------------------------
# Notion 同步
# -------------------------------
def sync_to_notion(md_path, config):
    if config.get("app.mock", False):
        logger.info(f"[notion_sync] Mock 模式：笔记内容不会同步到 Notion")
        return True

    notion_cfg = config.get("notion", {})
    token = notion_cfg.get("token")
    database_id = notion_cfg.get("database_id")
    tags = notion_cfg.get("tags", [])
    publish_status = notion_cfg.get("publish_status", "Published")

    if not token or not database_id:
        logger.warning("[notion_sync] 未配置 Notion token 或 database_id，跳过同步")
        return False

    client = Client(auth=token)
    md_content = read_markdown(md_path)
    title = os.path.basename(md_path).replace(".md", "")

    # 检查数据库是否已有同名条目
    existing_pages = client.databases.query(
        **{
            "database_id": database_id,
            "filter": {
                "property": "Name",
                "title": {"equals": title}
            }
        }
    ).get("results", [])

    if existing_pages:
        # 更新已有条目
        page_id = existing_pages[0]["id"]
        logger.info(f"[notion_sync] 更新已有条目: {title}")
        client.pages.update(
            page_id=page_id,
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
                "Status": {"select": {"name": publish_status}},
                "Tags": {"multi_select": [{"name": tag} for tag in tags]},
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"text": [{"type": "text", "text": {"content": md_content}}]}
                }
            ]
        )
    else:
        # 创建新条目
        logger.info(f"[notion_sync] 创建新条目: {title}")
        client.pages.create(
            parent={"database_id": database_id},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
                "Status": {"select": {"name": publish_status}},
                "Tags": {"multi_select": [{"name": tag} for tag in tags]},
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"text": [{"type": "text", "text": {"content": md_content}}]}
                }
            ]
        )
    logger.info(f"[notion_sync] 笔记同步完成: {title}")
    return True


# -------------------------------
# CLI 测试
# -------------------------------
if __name__ == "__main__":
    cfg = load_config()
    output_dir = cfg.get("output.markdown_path", "./notes")
    md_files = [f for f in os.listdir(output_dir) if f.endswith(".md")]
    if not md_files:
        logger.warning("[notion_sync] 目录没有 Markdown 文件可同步")
    else:
        for md_file in md_files:
            md_path = os.path.join(output_dir, md_file)
            sync_to_notion(md_path, cfg)
