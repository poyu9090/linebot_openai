import mysql.connector
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage,
    ButtonsTemplate, MessageTemplateAction, MessageTemplateAction
)
from facebook_scraper import get_posts
import time
from datetime import datetime, timedelta

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
    "database": "u266927754_poyu",
    "charset": "utf8mb4"
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
    # 獲取使用者的關鍵字列表
    keywords = check_user_keywords(user_id)
    keywords = keywords.split(',')  # 將關鍵字轉換為列表
    print(keywords)

    # 連接到資料庫
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # 創建包含關鍵字的查詢語句
    sql = "SELECT post_content, post_link, post_time FROM post_data WHERE post_time > %s AND ("
    for i in range(len(keywords)):
        if i != 0:
            sql += " AND "
        sql += "post_content LIKE %s"
    sql += ")"

    # 获取一周前的时间
    week_ago = datetime.now() - timedelta(weeks=1)
    week_ago_str = week_ago.strftime('%Y-%m-%d %H:%M:%S')

    # 執行 SQL 查詢
    cursor.execute(sql, (week_ago_str, ) + tuple(f"%{kw}%" for kw in keywords))

    results = cursor.fetchall()
    print(results)
    # 關閉連線
    cursor.close()
    conn.close()

    return results
    
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
                TemplateSendMessage(
                    alt_text='Buttons template',
                    template=ButtonsTemplate(
                        title='找房條件',
                        text=f'這是你目前設定的找房條件\n\n{keywords}',
                        actions=[
                            MessageTemplateAction(
                                label='開始找房',
                                text='開始找房'
                            ),
                            MessageTemplateAction(
                                label='找房條件',
                                text='找房條件'
                            ),
                            MessageTemplateAction(
                                label='更新找房條件',
                                text='更新找房條件'
                            ),
                            MessageTemplateAction(
                                label='客服服務',
                                text='客服服務'
                            )   
                        ]
                        
                    )
                )
            )
        else:
            save_user_state(user_id, "首次輸入找房條件")  # 先儲存用戶的回傳訊息
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請輸入您的找房條件\n\n若要設定復數個關鍵字，請用,區隔\n\n⭐ 範例：台北,大安區,套房")
            )
    elif message == "更新找房條件":
        save_user_state(user_id, "更新找房條件")  # 先儲存用戶的回傳訊息

        # 再等待用戶的下一句回傳訊息
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入您的找房條件\n\n若要設定復數個關鍵字\n\n請用半形的逗號做區隔\n\n⭐ 範例：台北,大安區,套房")
        )
        
    elif message == "開始找房":
       keywords = check_user_keywords(user_id)
       results = search_post(user_id)  # 將 search_post 函數的返回值指派給 results 變數
       if not results:
           line_bot_api.reply_message(
               event.reply_token,
               TemplateSendMessage(
                   alt_text='Buttons template',
                   template=ButtonsTemplate(
                       title='很抱歉，目前沒有符合您關鍵字條件的貼文',
                       text=f'建議您更改關鍵字條件，目前沒有完全符合的貼文\n\n這是你目前設定的找房條件\n\n{keywords}',
                       actions=[
                           MessageTemplateAction(
                               label='開始找房',
                               text='開始找房'
                           ),
                           MessageTemplateAction(
                               label='找房條件',
                               text='找房條件'
                           ),
                           MessageTemplateAction(
                               label='更新找房條件',
                               text='更新找房條件'
                           ),
                           MessageTemplateAction(
                               label='客服服務',
                               text='客服服務'
                           )
                       ]
                   )
               )  
           )
       else:
           for result in results:
               message = f"貼文時間：{result[2]}\n貼文連結：{result[1]}\n貼文內容：{result[0]}"
               line_bot_api.push_message(user_id, TextSendMessage(text=message))
               time.sleep(3)  # 等待一秒後再傳送下一條訊息
    
    else:
        state = check_user_state(user_id)
        if state == "更新找房條件":
            save_user_keywords(user_id, message)
            line_bot_api.reply_message(
                event.reply_token,
                TemplateSendMessage(
                    alt_text='Buttons template',
                    template=ButtonsTemplate(
                        title='找房條件',
                        text=f'更新完成！\n\n這是您目前設定的找房條件\n\n{message}',
                        actions=[
                            MessageTemplateAction(
                                label='開始找房',
                                text='開始找房'
                            ),
                            MessageTemplateAction(
                                label='找房條件',
                                text='找房條件'
                            ),
                            MessageTemplateAction(
                                label='更新找房條件',
                                text='更新找房條件'
                            ),
                            MessageTemplateAction(
                                label='客服服務',
                                text='客服服務'
                            )
                        ]
                    )
                )
            )
        elif state == "首次輸入找房條件":
            save_user_keywords(user_id, message)
            line_bot_api.reply_message(
                event.reply_token,
                TemplateSendMessage(
                    alt_text='Buttons template',
                    template=ButtonsTemplate(
                        title='找房條件',
                        text=f'設定完成！這是您目前設定的找房條件\n\n{message}',
                        actions=[
                            MessageTemplateAction(
                                label='開始找房',
                                text='開始找房'
                            ),
                            MessageTemplateAction(
                                label='找房條件',
                                text='找房條件'
                            ),
                            MessageTemplateAction(
                                label='更新找房條件',
                                text='更新找房條件'
                            ),
                            MessageTemplateAction(
                                label='客服服務',
                                text='客服服務'
                            )
                        ]
                    )
                )
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TemplateSendMessage(
                    alt_text='Buttons template',
                    template=ButtonsTemplate(
                        #title='找房條件',
                        text='哈囉您好～\n\n您可以使用以下按鈕開始找房或是找租客的服務喔！',
                        actions=[
                            MessageTemplateAction(
                                label='開始找房',
                                text='開始找房'
                            ),
                            MessageTemplateAction(
                                label='找房條件',
                                text='找房條件'
                            ),
                            MessageTemplateAction(
                                label='更新找房服務',
                                text='更新找房服務'
                            ),   
                            MessageTemplateAction(
                                label='客服服務',
                                text='客服服務'
                            )                                  
                        ]
                    )
                )
            )

if __name__ == "__main__":
    app.run()
