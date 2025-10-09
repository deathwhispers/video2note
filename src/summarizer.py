import os
from src.utils import ensure_dir, load_config, logger

# -------------------------------
# OpenAI 生成 Markdown
# -------------------------------
def summarize_with_openai(text, config):
    import openai
    providers = config.get("providers", {})
    openai_cfg = providers.get("openai", {})
    openai.api_key = openai_cfg.get("api_key")
    model = config.get("ai.model", "gpt-4o-mini")
    temperature = config.get("ai.temperature", 0.7)
    prompt_template = openai_cfg.get("prompt_template", "{{transcript}}")

    prompt = prompt_template.replace("{{transcript}}", text)

    logger.info(f"[summarizer] 调用 OpenAI LLM 生成 Markdown 笔记 ...")
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )
    md_text = response.choices[0].message.content
    return md_text


# -------------------------------
# Mock 模式
# -------------------------------
def summarize_with_mock(text, config):
    logger.info("[summarizer] Mock 模式生成 Markdown")
    return f"# 模拟笔记\n\n{text[:200]}...\n\n## 章节示例\n- 概述\n- 原理图\n- 代码讲解\n- 应用场景"


# -------------------------------
# 其他厂商可扩展
# -------------------------------
def summarize_with_gemini(text, config):
    logger.info("[summarizer] Gemini 生成笔记暂未实现，使用 mock")
    return summarize_with_mock(text, config)

def summarize_with_qwen(text, config):
    logger.info("[summarizer] Qwen 生成笔记暂未实现，使用 mock")
    return summarize_with_mock(text, config)

def summarize_with_ernie(text, config):
    logger.info("[summarizer] Ernie 生成笔记暂未实现，使用 mock")
    return summarize_with_mock(text, config)

def summarize_with_vllm(text, config):
    logger.info("[summarizer] VLLM 生成笔记暂未实现，使用 mock")
    return summarize_with_mock(text, config)


# -------------------------------
# 统一接口
# -------------------------------
def summarize(text, config):
    if config.get("app.mock", False):
        return summarize_with_mock(text, config)

    provider = config.get("ai.provider", "openai").lower()
    if provider == "openai":
        return summarize_with_openai(text, config)
    elif provider == "gemini":
        return summarize_with_gemini(text, config)
    elif provider == "qwen":
        return summarize_with_qwen(text, config)
    elif provider == "ernie":
        return summarize_with_ernie(text, config)
    elif provider == "vllm":
        return summarize_with_vllm(text, config)
    else:
        logger.warning(f"[summarizer] 未知 provider {provider}，使用 mock")
        return summarize_with_mock(text, config)


# -------------------------------
# 保存 Markdown 文件
# -------------------------------
def save_markdown(md_text, output_dir, filename="note.md"):
    ensure_dir(output_dir)
    file_path = os.path.join(output_dir, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    logger.info(f"[summarizer] Markdown 笔记已保存: {file_path}")
    return file_path


# -------------------------------
# CLI 测试
# -------------------------------
if __name__ == "__main__":
    cfg = load_config()
    # 假设 transcriber 输出的文本
    sample_text = "这是转写后的示例文本，用于生成 Markdown 笔记。"
    md = summarize(sample_text, cfg)
    output_dir = cfg.get("output.markdown_path", "./notes")
    save_markdown(md, output_dir)
