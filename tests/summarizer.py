import os

from utils import ensure_dir, logger

def save_markdown(md_text, output_dir, filename="note.md"):
    ensure_dir(output_dir)
    file_path = os.path.join(output_dir, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    logger.info(f"[summarizer] 笔记已保存: {file_path}")
    return file_path

def summarize_with_rules(full_transcript, config, frames=None):
    """用规则生成结构化Markdown，无需模型"""
    md = []
    # 1. 标题
    video_title = config.get("video", {}).get("source", "视频笔记").split("/")[-1]
    md.append(f"# {video_title} 笔记")

    # 2. 概述（取前300字）
    md.append("## 概述")
    md.append(full_transcript[:300] + "...")

    # 3. 完整字幕
    if "[字幕内容]" in full_transcript:
        md.append("## 字幕内容")
        md.append(full_transcript.split("[字幕内容]")[1].split("[音频转写]")[0].strip())

    # 4. 完整音频转写
    if "[音频转写]" in full_transcript:
        md.append("## 音频转写")
        md.append(full_transcript.split("[音频转写]")[1].strip())

    # 5. 关键帧引用
    if frames:
        md.append("## 关键帧")
        for i, frame in enumerate(frames[:5]):  # 只展示前5张
            md.append(f"![关键帧{i + 1}]({frame})")

    return "\n\n".join(md)

def summarize_with_light_nlp(full_transcript, config, frames=None):
    """用轻量NLP库生成笔记"""
    import spacy
    from nltk.tokenize import sent_tokenize

    nlp = spacy.load("zh_core_web_sm")  # 加载中文NLP模型
    doc = nlp(full_transcript[:5000])  # 取前5000字处理

    # 提取关键词
    keywords = [ent.text for ent in doc.ents if ent.label_ in ["PERSON", "ORG", "GPE", "PRODUCT"]]

    # 分割段落
    sentences = sent_tokenize(full_transcript)
    chunks = [sentences[i:i+5] for i in range(0, len(sentences), 5)]  # 每5句一段

    # 生成MD
    md = [f"# 视频笔记（关键词：{', '.join(keywords[:5])}）"]
    md.append("## 核心内容")
    for i, chunk in enumerate(chunks[:3]):  # 前3段
        md.append(f"### 段落{i+1}")
        md.append(" ".join(chunk))

    # 关键帧
    if frames:
        md.append("## 关键帧")
        md.extend([f"![帧{i}]({f})" for i, f in enumerate(frames[:3])])

    return "\n\n".join(md)


def summarize_with_local(text, config, frames=None):
    providers = config.get("providers", {})
    local_cfg = providers.get("local", {})
    summarizer = local_cfg.get("summarizer", "rules")
    if summarizer == "rules":
        return summarize_with_rules(text, config, frames)
    elif summarizer == "light-nlp":
        return summarize_with_light_nlp(text, config, frames)
    else:
        logger.warning(f"未知local summarizer {local_cfg.get('summarizer')}，使用mock")
        return summarize_with_mock(text, config, frames)


def summarize_with_openai(text, config, frames=None):
    import openai
    providers = config.get("providers", {})
    openai_cfg = providers.get("openai", {})
    openai.api_key = openai_cfg.get("api_key")
    model = config.get("ai", {}).get("model", "gpt-4o-mini")
    temperature = config.get("ai", {}).get("temperature", 0.7)
    prompt_template = openai_cfg.get("prompt_template", "{{transcript}}")

    # 处理图片路径
    frames_str = "\n".join(frames) if frames else "无图片"
    prompt = prompt_template.replace("{{transcript}}", text).replace("{{frames}}", frames_str)

    logger.info("[summarizer] 调用OpenAI生成笔记...")
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )
    return response.choices[0].message.content


def summarize_with_mock(text, config, frames=None):
    frames_str = "\n".join(frames) if frames else "无图片"
    return f"# 模拟笔记\n\n## 转写内容\n{text[:200]}...\n\n## 图片\n{frames_str}"


# -------------------------------
# 新增：豆包摘要生成
# -------------------------------
def summarize_with_doubao(text, config, frames=None):
    import requests

    doubao_cfg = config.get("providers", {}).get("doubao", {})
    api_key = doubao_cfg.get("api_key")
    endpoint = doubao_cfg.get("endpoint", "https://api.doubao.com/v1/chat/completions")
    if not api_key:
        raise ValueError("豆包API密钥未配置（providers.doubao.api_key）")

    model = config.get("ai", {}).get("model", "doubao-pro")
    temperature = config.get("ai", {}).get("temperature", 0.7)
    prompt_template = doubao_cfg.get("prompt_template", "{{transcript}}")

    # 处理图片和转写内容
    frames_str = "\n".join(frames) if frames else "无图片"
    prompt = prompt_template.replace("{{transcript}}", text).replace("{{frames}}", frames_str)

    logger.info(f"[summarizer] 调用豆包模型 {model} 生成笔记")
    try:
        response = requests.post(
            url=endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"[summarizer] 豆包生成失败：{str(e)}")
        raise


# -------------------------------
# 新增：DeepSeek摘要生成
# -------------------------------
def summarize_with_deepseek(text, config, frames=None):
    import requests

    deepseek_cfg = config.get("providers", {}).get("deepseek", {})
    api_key = deepseek_cfg.get("api_key")
    endpoint = deepseek_cfg.get("endpoint", "https://api.deepseek.com/v1/chat/completions")
    if not api_key:
        raise ValueError("DeepSeek API密钥未配置（providers.deepseek.api_key）")

    model = config.get("ai", {}).get("model", "deepseek-chat")
    temperature = config.get("ai", {}).get("temperature", 0.7)
    prompt_template = deepseek_cfg.get("prompt_template", "{{transcript}}")

    frames_str = "\n".join(frames) if frames else "无图片"
    prompt = prompt_template.replace("{{transcript}}", text).replace("{{frames}}", frames_str)

    logger.info(f"[summarizer] 调用DeepSeek模型 {model} 生成笔记")
    try:
        response = requests.post(
            url=endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"[summarizer] DeepSeek生成失败：{str(e)}")
        raise


# -------------------------------
# 修复：通义千问（Qwen）真实摘要生成
# -------------------------------
def summarize_with_qwen(text, config, frames=None):
    import dashscope

    qwen_cfg = config.get("providers", {}).get("qwen", {})
    api_key = qwen_cfg.get("api_key")
    if not api_key:
        raise ValueError("通义千问API密钥未配置（providers.qwen.api_key）")
    dashscope.api_key = api_key

    model = config.get("ai", {}).get("model", "qwen-plus")
    temperature = config.get("ai", {}).get("temperature", 0.7)
    prompt_template = qwen_cfg.get("prompt_template", "{{transcript}}")

    frames_str = "\n".join(frames) if frames else "无图片"
    prompt = prompt_template.replace("{{transcript}}", text).replace("{{frames}}", frames_str)

    logger.info(f"[summarizer] 调用通义千问模型 {model} 生成笔记")
    try:
        response = dashscope.Generation.call(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        if response.status_code == dashscope.StatusCode.SUCCESS:
            return response.output["text"]
        else:
            raise Exception(f"API错误: {response.message}")
    except Exception as e:
        logger.error(f"[summarizer] 通义千问生成失败：{str(e)}")
        raise


# -------------------------------
# 更新主摘要函数（添加新供应商）
# -------------------------------
def summarize(text, config, frames=None):
    if config.get("app", {}).get("mock", False):
        return summarize_with_mock(text, config, frames)

    provider = config.get("ai", {}).get("provider", "openai").lower()
    if provider == "openai":
        return summarize_with_openai(text, config, frames)
    elif provider == "qwen":
        return summarize_with_qwen(text, config, frames)  # 替换原占位函数
    elif provider == "doubao":
        return summarize_with_doubao(text, config, frames)  # 新增
    elif provider == "deepseek":
        return summarize_with_deepseek(text, config, frames)  # 新增
    elif provider == "local":
        return summarize_with_local(text, config, frames)
    else:
        logger.warning(f"未知provider {provider}，使用mock")
        return summarize_with_mock(text, config, frames)

