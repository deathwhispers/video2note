# src/video2note/notion/md_parser.py

from notion_client import block as notion_block

def markdown_to_notion_blocks(md_text: str, frames: list[str] = None) -> list[dict]:
    """
    把 Markdown 文本 + frames 列表 转换为 Notion API 可用的 blocks 列表。
    这里只是一个简化示例：处理标题、段落、图片链接。
    """
    blocks = []
    lines = md_text.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("# "):
            # 一级标题 -> heading_1
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"text": {"content": line[2:]}}]}
            })
        elif line.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": line[3:]}}]}
            })
        elif line.startswith("![" ) and "(" in line and ")" in line:
            # 图片 Markdown 语法 ![alt](url)
            start = line.find("(")
            end = line.find(")", start)
            url = line[start+1:end]
            blocks.append({
                "object": "block",
                "type": "image",
                "image": {
                    "type": "external",
                    "external": {"url": url}
                }
            })
        else:
            # 普通段落
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": line}}]}
            })
    return blocks
