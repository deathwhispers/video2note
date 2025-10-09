import os
from utils import ensure_dir, timestamp, load_yaml
from downloader import download_video
from transcriber import transcribe
from summarizer import summarize
from notion_sync import sync_to_notion

# -----------------------------
# 加载配置
# -----------------------------
config = load_yaml("config/config.yaml")
providers = load_yaml("config/providers.yaml")["providers"]

video_cfg = config["video"]
output_cfg = config["output"]
ai_cfg = config["ai"]
notion_cfg = config.get("notion", {})

# -----------------------------
# 下载视频
# -----------------------------
video_file = download_video(video_cfg["source"], video_cfg["download_path"])

# -----------------------------
# 选择 AI 供应商
# -----------------------------
provider_name = ai_cfg.get("default_provider", "openai")
provider_config = providers.get(provider_name, {})
provider_config["name"] = provider_name  # 确保传入模块

# -----------------------------
# 转写
# -----------------------------
transcript = transcribe(video_file, provider_config, language=video_cfg.get("language", "zh"))

# -----------------------------
# 生成摘要
# -----------------------------
summary = summarize(transcript, provider_config, temperature=ai_cfg.get("temperature", 0.7))

# -----------------------------
# 保存 Markdown
# -----------------------------
ensure_dir(output_cfg["markdown_path"])
md_file = os.path.join(output_cfg["markdown_path"], f"note_{timestamp()}.md")
with open(md_file, "w", encoding="utf-8") as f:
    f.write(f"# 视频笔记\n\n## 视频文件\n{video_file}\n\n## 转写文本\n{transcript}\n\n## 摘要\n{summary}\n")
print(f"[main] Markdown saved to {md_file}")

# -----------------------------
# 同步到 Notion
# -----------------------------
sync_to_notion(summary, notion_cfg)
