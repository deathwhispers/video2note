# src/video2note/core/exceptions.py

class Video2NoteError(Exception):
    """顶层通用错误"""

class DownloadError(Video2NoteError):
    """下载阶段错误"""

class TranscriptionError(Video2NoteError):
    """转写阶段错误"""

class SummarizationError(Video2NoteError):
    """摘要 / 笔记生成错误"""

class SyncError(Video2NoteError):
    """同步 / Notion 相关错误"""
