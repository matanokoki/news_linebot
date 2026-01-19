# 🚀 Raspberry Pi Server Deployment Guide

このBotをRaspberry Piで24時間稼働させるためのセットアップ手順です。
Pythonの自動起動と、ngrokを使った固定ドメインによる外部公開をSystemdで管理します。

## 1. Prerequisites (事前準備)
* Raspberry Pi (Raspberry Pi OS Bookworm推奨)
* ngrok Account (Free plan ok)
* LINE Developers Channel

## 2. Setup Project
ラズパイにSSH接続し、リポジトリをCloneして仮想環境を構築します。

```bash
# Clone repository
cd ~
git clone [https://github.com/YourUserName/YourRepoName.git](https://github.com/YourUserName/YourRepoName.git)
cd YourRepoName

# Setup venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Environment Variables
プロジェクトルートに .env ファイルを作成します。
```bash
nano .env
```
```ini, TOML
LINE_CHANNEL_ACCESS_TOKEN="your_token"
LINE_CHANNEL_SECRET="your_secret"
GEMINI_API_KEY="your_key"
```
## 4. Install ngrok (Manual Install)
apt 経由では不安定な場合があるため、バイナリを直接配置します。
```Bash
cd ~
wget [https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm64.tgz](https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm64.tgz)
sudo tar xvzf ngrok-v3-stable-linux-arm64.tgz -C /usr/local/bin

# Check installation
ngrok --version
```
ngrokのダッシュボードからAuthtokenを取得し、登録します。
```bash
ngrok config add-authtoken <YOUR_AUTHTOKEN>
```
## 5. Systemd Service Setup (Python Bot)
Bot本体を自動起動する設定です。 パス（/home/pi/...）やユーザー名は環境に合わせて変更してください。
```bash
sudo nano /etc/systemd/system/linebot.service
```
```Ini, TOML
[Unit]
Description=Line AI Butler Service
After=network.target

[Service]
# ユーザー名に注意 (pi or slackbot etc...)
User=pi
Group=pi
WorkingDirectory=/home/pi/news-linebot
ExecStart=/home/pi/news-linebot/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
## 6. Systemd Service Setup (ngrok Tunnel)
ngrokで固定ドメインを使って公開する設定です。 ※ 事前にngrokダッシュボードの「Domains」で固定ドメインを取得してください。
```bash
sudo nano /etc/systemd/system/ngrok.service
```
```Ini, TOML
[Unit]
Description=ngrok Tunnel
After=network.target

[Service]
User=pi
# --domain フラグで固定ドメインを指定
ExecStart=/usr/local/bin/ngrok http --domain=your-static-domain.ngrok-free.app 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
## 7. Enable Services
サービスを登録して起動します。
```bash
sudo systemctl daemon-reload

# Start Bot
sudo systemctl enable linebot
sudo systemctl start linebot

# Start Tunnel
sudo systemctl enable ngrok
sudo systemctl start ngrok
```
## 8. Final Check
ステータスを確認し、エラーが出ていないかチェックします。
```bash
sudo systemctl status linebot
sudo systemctl status ngrok
```
最後に、LINE Developersコンソールの Webhook URL を更新します： https://your-static-domain.ngrok-free.app/callback