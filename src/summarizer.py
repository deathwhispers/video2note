import time
import requests
import json
import openai

def summarize(transcript, provider_config, temperature=0.7):
    provider = provider_config.get("name", "openai")
    prompt_template = provider_config.get("prompt_template", "")
    prompt = prompt_template.replace("{{transcript}}", transcript)

    if provider == "openai":
        openai.api_key = provider_config.get("api_key")
        response = openai.ChatCompletion.create(
            model=provider_config.get("models", ["gpt-4o-mini"])[0],
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        summary = response.choices[0].message.content

    elif provider == "anthropic":
        summary = "模拟Anthropic生成摘要"
    elif provider == "gemini":
        summary = "模拟Gemini生成摘要"
    elif provider == "qwen":
        summary = "模拟Qwen生成摘要"
    elif provider == "ernie":
        summary = "模拟Ernie生成摘要"
    elif provider == "vllm":
        summary = "模拟vLLM生成摘要"
    else:
        summary = "模拟摘要"

    print(f"[summarizer] {provider} summary completed")
    return summary
