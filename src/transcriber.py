import os
import subprocess
import time
import requests
import json
import openai

def transcribe(video_file, provider_config, language="zh"):
    provider = provider_config.get("name", "openai")

    # 音频提取
    audio_file = video_file.replace(".mp4", ".mp3")
    if not os.path.exists(audio_file):
        subprocess.run([
            "ffmpeg", "-y", "-i", video_file, "-vn", "-acodec", "mp3", audio_file
        ], check=True)
        print(f"[transcriber] Extracted audio to {audio_file}")

    if provider == "openai":
        openai.api_key = provider_config.get("api_key")
        with open(audio_file, "rb") as f:
            transcript_response = openai.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language=language
            )
        transcript = transcript_response.text

    elif provider == "anthropic":
        api_key = provider_config.get("api_key")
        url = provider_config.get("endpoint")
        # 这里假设音频已经转文本，直接模拟
        transcript = "模拟Anthropic转写文本"
        # 可以根据实际 API 调用
    elif provider == "gemini":
        transcript = "模拟Gemini转写文本"
    elif provider == "qwen":
        transcript = "模拟Qwen转写文本"
    elif provider == "ernie":
        transcript = "模拟Ernie转写文本"
    elif provider == "vllm":
        transcript = "模拟vLLM转写文本"
    else:
        transcript = "模拟转写文本"

    print(f"[transcriber] {provider} transcription completed")
    return transcript
