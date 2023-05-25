from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 設定 Line Bot 的基本資訊
channel_secret = "de3c0becd65442f8051eb776d1ac4704"
channel_access_token = "2i1ezDbaoDHmdVvIlfhnwVZxINI2ziI1Dwk00TIy9TB38XfkBXe/FZr+ON1z01c0+EB2tqupVKXlEKmNc3yRtatXRLd0GEmUMaMEeK4QiqQxwbDIfZSjrewlLG3ktGxygNep8yr9d3Z2a+7xZdZQDQdB04t89/1O/w1cDnyilFU="

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

@app.route("/", methods=["GET"])
def index():
    return "Hello, this is your Line Bot!"


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message)
    )

if __name__ == "__main__":
    app.run()
