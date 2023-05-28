import mysql.connector
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from facebook_scraper import get_posts
import time

app = Flask(__name__)

# 設定 Line Bot 的基本資訊
channel_secret = "de3c0becd65442f8051eb776d1ac4704"
channel_access_token = "2i1ezDbaoDHmdVvIlfhnwVZxINI2ziI1Dwk00TIy9TB38XfkBXe/FZr+ON1z01c0+EB2tqupVKXlEKmNc3yRtatXRLd0GEmUMaMEeK4QiqQxwbDIfZSjrewlLG3ktGxygNep8yr9d3Z2a+7xZdZQDQdB04t89/1O/w1cDnyilFU="

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# 資料庫連線設定
db_config = {
    "host": "217.21.74.1",
    "user": "u266927754_poyu9090",
    "password": "Jjooee9090!",
    "database": "u266927754_poyu"
}

def check_user_keywords(user_id):
    # 連線到資料庫
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # 執行 SQL 命令，查詢資料庫中是否有該使用者的資料
    sql = "SELECT keywords FROM test WHERE user_id = %s"
    cursor.execute(sql, (user_id,))
    result = cursor.fetchone()

    # 關閉連線
    cursor.close()
    conn.close()

    if result:
        # 如果有資料，返回該使用者的找房條件
        return result[0]
    else:
        # 如果沒有資料，返回空字串
        return ""

def save_user_keywords(user_id, data):
    # 連線到資料庫
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # 執行 SQL 命令，更新資料庫中對應的使用者資料
    sql = "UPDATE test SET keywords = %s, state = NULL WHERE user_id = %s"
    cursor.execute(sql, (data, user_id))

    # 提交變更
    conn.commit()

    # 關閉連線
    cursor.close()
    conn.close()
 
def check_user_state(user_id):
    # 連線到資料庫
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # 執行 SQL 命令，查詢資料庫中是否有該使用者的資料
    sql = "SELECT state FROM test WHERE user_id = %s"
    cursor.execute(sql, (user_id,))
    result = cursor.fetchone()

    # 關閉連線
    cursor.close()
    conn.close()

    if result:
        # 如果有資料，返回該使用者的狀態
        return result[0]
    else:
        # 如果沒有資料，返回空字串
        return ""

def save_user_state(user_id, data):
    # 連線到資料庫
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # 執行 SQL 命令，更新資料庫中對應的使用者資料
    sql = "UPDATE test SET state = %s WHERE user_id = %s"
    cursor.execute(sql, (data, user_id))

    # 提交變更
    conn.commit()

    # 關閉連線
    cursor.close()
    conn.close()

def check_user_exists(user_id):
    # 連線到資料庫
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # 執行 SQL 命令，查詢資料庫中是否有該使用者的資料
    sql = "SELECT user_id FROM test WHERE user_id = %s"
    cursor.execute(sql, (user_id,))
    result = cursor.fetchone()

    # 關閉連線
    cursor.close()
    conn.close()

    return bool(result)

def save_user_id(user_id):
    # 連線到資料庫
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # 執行 SQL 命令，將 user_id 新增到資料庫
    sql = "INSERT INTO test (user_id) VALUES (%s)"
    cursor.execute(sql, (user_id,))

    # 提交變更
    conn.commit()

    # 關閉連線
    cursor.close()
    conn.close()
    
def search_post(user_id):
    group_name1 = '464870710346711'
    group_name2 = '459966811445588'
    keywords = check_user_keywords(user_id)
    print(f"keywords{keywords}")

    if not keywords:
        line_bot_api.push_message(user_id, TextSendMessage(text="你需要先設定 keywords 喔"))
        return

    # 搜尋社團一的貼文，並逐一檢查每個貼文
    print(f'-----------開始從社團一開始找-----------')

    found_posts = []  # 存储找到的帖子
    for post in get_posts(group=group_name1, pages=3, cookies='cookies.txt'):
        post_id = post['post_id']
        post_text = post['text']
        print(f"儲存貼文中:{post_id}")
        #if any(keyword in post_text for keyword in keywords):  # 如果这个帖子包含指定的关键字
            #found_posts.append(post)  # 将符合条件的帖子添加到列表中

    if found_posts:
        messages = []
        for post in found_posts:
            message = f"找到符合条件的贴文囉！:\n{post['post_url']}\n{post['text'][:300]}"
            messages.append(TextSendMessage(text=message))

        try:
            line_bot_api.reply_message(user_id, messages)  # 一次性发送所有帖子消息
            print(f'找到{len(found_posts)}篇贴文')
            
        except LineBotApiError as e:
            print(f'Line Bot发送消息失败: {e.error.message}')
    else:
        print(f'未找到符合条件的贴文')

    time.sleep(3)  # 等待 3 秒钟，以避免被 Facebook 检测为机器人

    
@app.route("/", methods=["GET"])
def index():
    return "Hello, this is your Line Bot!"

@app.route("/update_database", methods=["POST"])
def update_database():
    group_name = '464870710346711'  # 替換為你要擷取貼文的社團ID
    posts = get_posts(group=group_name, pages=3, cookies='cookies.txt')  # 根據需求設定擷取的頁數

    # 連線到資料庫
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    for post in posts:
        post_time = post['time']
        post_url = post['post_url']
        post_content = post['text']

        # 執行 SQL 命令，將貼文資訊插入資料庫
        sql = "INSERT INTO post_data (post_time, post_url, post_content) VALUES (%s, %s, %s)"
        cursor.execute(sql, (post_time, post_url, post_content))

    # 提交變更
    conn.commit()

    # 關閉連線
    cursor.close()
    conn.close()

    return "OK"

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
    user_id = event.source.user_id
    message = event.message.text

    # 檢查 user_id 是否存在於資料庫中
    if not check_user_exists(user_id):
        # 若不存在，新增 user_id 到資料庫
        save_user_id(user_id)

    if message == "找房條件":
        keywords = check_user_keywords(user_id)
        if keywords:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"您目前的找房條件是：{keywords} \n 需要更新找房條件請輸入『更新找房資料』")
            )
        else:
            save_user_state(user_id, "首次輸入找房條件")  # 先儲存用戶的回傳訊息
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請輸入找房條件")
            )
    elif message == "更新找房資料":
        save_user_state(user_id, "更新找房資料")  # 先儲存用戶的回傳訊息

        # 再等待用戶的下一句回傳訊息
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入新的找房條件")
        )
        
    elif message == "開始找房":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="系統正開始幫妳找房請稍等")
        )
        search_post(user_id)

    else:
        state = check_user_state(user_id)
        if state == "更新找房資料":
            save_user_keywords(user_id, message)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"已更新您的找房條件：{message}")
            )
        elif state == "首次輸入找房條件":
            save_user_keywords(user_id, message)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"已儲存您的找房條件：{message}")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請輸入有效指令")
            )

if __name__ == "__main__":
    app.run()
