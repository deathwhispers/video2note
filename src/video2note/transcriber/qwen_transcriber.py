from video2note.transcriber.base import Transcriber
from video2note.types.transcript import Transcript, Segment
from video2note.core.exceptions import TranscriptionError
from video2note.utils.logger import logging

import dashscope  # 你原来使用的库

class QwenTranscriber(Transcriber):
    def __init__(self, config):
        super().__init__(config)
        cfg = config.providers.qwen
        self.api_key = cfg.api_key
        if not self.api_key:
            raise ValueError("Qwen API key not configured")
        self.asr_model = cfg.asr_model

    def transcribe(self, audio_path: str) -> Transcript:
        if not audio_path or not os.path.exists(audio_path):
            raise TranscriptionError(f"Audio file does not exist: {audio_path}")

        logging.info(f"[QwenTranscriber] 转写音频 {audio_path} 模型 {self.asr_model}")

        language_hint = getattr(self.config.video, "language", "zh")
        language_prompts = {
            "zh": "请将音频内容逐字转写为中文文本，不要总结。",
            "en": "Please transcribe the audio content verbatim into English text.",
            "ja": "音声内容を逐語的に日本語テキストに書き起こしてください。",
            "ko": "오디오 내용을 한글 텍스트로 충실하게 받아쓰기 하세요。"
        }
        prompt_text = language_prompts.get(language_hint, "Transcribe the audio.")

        try:
            response = dashscope.Generation.call(
                model="paraformer-v2",
                api_key=self.api_key,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"audio": audio_path},
                            {"text": prompt_text}
                        ]
                    }
                ]
            )
        except Exception as e:
            logging.error(f"[QwenTranscriber] 请求失败: {e}")
            raise TranscriptionError(f"Qwen ASR request failed: {e}")

        # 解析响应
        if response.status_code == 200:
            choices = response.output.get("choices", [])
            if not choices:
                raise TranscriptionError("Qwen ASR returned empty choices")
            content = choices[0].get("message", {}).get("content", "").strip()
            seg = Segment(start=0.0, end=0.0, text=content)
            return Transcript([seg])
        else:
            raise TranscriptionError(f"Qwen ASR failed [code={response.code}]: {response.message}")
