# LINE AI Summary Butler (AI要約執事)

LINEグループで共有された「Webニュース記事」や「YouTube動画」の内容を、Google Gemini APIを使って自動で要約してくれるAIボットです。
家族や友人グループでの情報共有をスムーズにするために開発されました。

## 🚀 Features (機能)

* **Web記事要約:** URLを送ると、広告などを除外して本文のみを抽出し、3行で要約します。
* **YouTube動画要約:** 動画の字幕データを取得し、内容を要約します（字幕付き動画に対応）。
* **名前呼び出しトリガー:** 会話の邪魔にならないよう、「執事」（または設定した名前）と呼びかけた時だけ反応します。
* **高速レスポンス:** FastAPIの非同期処理（BackgroundTasks）を利用し、LINEサーバーのタイムアウトを回避しています。
* **RAG的アプローチ:** 記事本文をプロンプトに含めてAPIに投げるため、ハルシネーション（嘘の生成）を抑制しています。

## 🛠 Tech Stack (使用技術)

* **Language:** Python 3.x
* **Framework:** FastAPI (Uvicorn)
* **AI Model:** Google Gemini 1.5 Flash
* **Platform:** LINE Messaging API
* **Libraries:**
    * `trafilatura`: Webスクレイピング・本文抽出
    * `youtube-transcript-api`: YouTube字幕取得
    * `line-bot-sdk`: LINE Bot SDK
* **Infrastructure:** Raspberry Pi (Home Server) + Cloudflare Tunnel (予定)

## ⚙️ Setup (セットアップ)

### 1. Clone & Install

```bash
git clone [https://github.com/YourUsername/line-ai-butler.git](https://github.com/YourUsername/line-ai-butler.git)
cd line-ai-butler
pip install -r requirements.txt
```

### 2. Environment Variables
プロジェクトルートに `.env` ファイルを作成し、以下のキーを設定してください。

```ini
LINE_CHANNEL_ACCESS_TOKEN="your_line_channel_access_token"
LINE_CHANNEL_SECRET="your_line_channel_secret"
GEMINI_API_KEY="your_gemini_api_key"
```

### 3. Run
```bash
python main.py
```

デフォルトでは `http://0.0.0.0:8000` で起動します。
外部公開には Cloudflare Tunnel や ngrok などを利用して、LINE DevelopersコンソールのWebhook URLに設定してください。

## 📝 Usage (使い方)

LINEのトーク画面で、以下のように話しかけてください。

> 執事 https://news.yahoo.co.jp/articles/xxxxx
>
> 執事 https://www.youtube.com/watch?v=xxxxx

## 👨‍💻 Author
Koki