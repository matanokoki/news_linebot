import os
import re
import logging
from urllib.parse import urlparse, parse_qs
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)
import trafilatura
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

# 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# ★ここを変更：呼び出すときの名前
BOT_NAME = "ひでまろ" 

genai.configure(api_key=GEMINI_API_KEY)
# モデルは確認済みのものを使用 (例: gemini-1.5-flash または gemini-pro)
model = genai.GenerativeModel('models/gemini-flash-lite-latest')

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = FastAPI()
logger = logging.getLogger("uvicorn")

# URL抽出用の正規表現
URL_PATTERN = r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+'

def get_youtube_video_id(url):
    """URLからYouTubeの動画IDを抽出する"""
    parsed = urlparse(url)
    if parsed.hostname in ['www.youtube.com', 'youtube.com']:
        return parse_qs(parsed.query).get('v', [None])[0]
    elif parsed.hostname == 'youtu.be':
        return parsed.path[1:]
    return None

def get_youtube_transcript(video_id):
    """古いライブラリでも動く＆自動生成も狙う版"""
    try:
        # 言語コードをたくさん指定して、どれか引っかかるのを待つ
        # 'ja' = 日本語, 'en' = 英語, 'ja-JP' = 日本語(地域指定)
        languages = [
            'ja', 'ja-JP', 'en', 'en-US', 
            'en-GB', 'ko', 'zh-Hant', 'zh-Hans'
        ]
        
        # cookies引数は最近の仕様変更で必要になることがあるが、一旦なしでトライ
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        
        full_text = " ".join([t['text'] for t in transcript_list])
        return full_text
        
    except Exception as e:
        logger.error(f"YouTube transcript error: {e}")
        return None

def scrape_and_summarize(url: str) -> str:
    """URL(Web/YouTube)の内容を取得して要約する"""
    content_text = ""
    source_type = "Web記事"

    # 1. YouTubeかどうか判定
    video_id = get_youtube_video_id(url)
    
    if video_id:
        # YouTubeの場合
        source_type = "YouTube動画"
        transcript = get_youtube_transcript(video_id)
        if transcript:
            content_text = transcript
        else:
            return "動画の字幕が取得できませんでした。（字幕オフの動画か、長すぎる可能性があります）"
    else:
        # 通常のWeb記事の場合
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                content_text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        except Exception:
            pass
    
    if not content_text or len(content_text) < 50:
        return f"{source_type}の内容をうまく読み取れませんでした。"

    # 2. Geminiへのプロンプト
    prompt = f"""
    以下の{source_type}の内容を、家族のLINEグループで共有するために要約してください。
    
    【制約事項】
    ・内容は絶対に捏造しないでください。
    ・専門用語は噛み砕いて説明してください。
    ・以下のフォーマットで出力してください。
    
    タイトル: [内容から推測されるタイトル]
    
    要点（3行まとめ）:
    ・[要点1]
    ・[要点2]
    ・[要点3]
    
    ひとこと: [家族へのコメントや、動画/記事の感想を1文で]
    
    【対象テキスト】
    {content_text[:15000]} 
    """
    # YouTube字幕は長いことが多いので文字数制限を少し緩和(15000)

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return "要約の生成中にエラーが発生しました。"

def handle_message_background(event, url):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        summary = scrape_and_summarize(url)
        try:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=summary)]
                )
            )
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

@app.post("/callback")
async def callback(request: Request, background_tasks: BackgroundTasks):
    signature = request.headers.get('X-Line-Signature', '')
    body = await request.body()
    body_str = body.decode('utf-8')

    try:
        events = handler.parser.parse(body_str, signature)
        
        for event in events:
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
                text = event.message.text
                
                # ★修正：名前呼び出しチェック
                # 「執事」が含まれている場合のみ処理に進む
                if BOT_NAME in text:
                    match = re.search(URL_PATTERN, text)
                    if match:
                        url = match.group()
                        background_tasks.add_task(handle_message_background, event, url)
                    else:
                        # 名前は呼ばれたけどURLがない場合の反応（オプション）
                        # 不要ならこのelseブロックは削除してもOK
                        pass 
                    
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    return "OK"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)