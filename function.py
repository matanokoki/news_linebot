from youtube_transcript_api import YouTubeTranscriptApi
import inspect

print("=== 診断開始 ===")
print(f"Type: {type(YouTubeTranscriptApi)}")
print(f"File: {inspect.getfile(YouTubeTranscriptApi)}")
print("Attributes:")
print(dir(YouTubeTranscriptApi))
print("=== 診断終了 ===")