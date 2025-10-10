import os

from src.utils import logger

try:
    from notion_client import Client
except ImportError:
    logger.warning("安装notion依赖...")
    import subprocess, sys

    subprocess.check_call([sys.executable, "-m", "pip", "install", "notion-client"])
    from notion_client import Client


def read_markdown(md_path):
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Markdown不存在: {md_path}")
    with open(md_path, "r", encoding="utf-8") as f:
        return f.read()


def sync_to_notion(md_path, config, frames=None):
    if config.get("app", {}).get("mock", False):
        logger.info("[notion] Mock模式：跳过同步")
        return True

    notion_cfg = config.get("notion", {})
    token = notion_cfg.get("token")
    database_id = notion_cfg.get("database_id")
    if not token or not database_id:
        logger.warning("[notion] 未配置token或database_id，跳过同步")
        return False

    client = Client(auth=token)
    md_content = read_markdown(md_path)
    title = os.path.basename(md_path).replace(".md", "")

    # 替换本地图片路径为Notion格式（实际需上传图片，此处简化）
    if frames:
        for frame in frames:
            md_content = md_content.replace(frame, f"![帧]({frame})")

    # 解析Markdown为Notion块
    blocks = read_markdown(md_content)

    # 检查是否已存在
    existing = client.databases.query(
        database_id=database_id,
        filter={"property": "Name", "title": {"equals": title}}
    ).get("results", [])

    if existing:
        client.pages.update(
            page_id=existing[0]["id"],
            properties={"Name": {"title": [{"text": {"content": title}}]}},
            children=blocks
        )
        logger.info(f"[notion] 更新页面: {title}")
    else:
        client.pages.create(
            parent={"database_id": database_id},
            properties={"Name": {"title": [{"text": {"content": title}}]}},
            children=blocks
        )
        logger.info(f"[notion] 创建页面: {title}")
    return True
