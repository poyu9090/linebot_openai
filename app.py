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
import datetime, timedelta
import threading



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
    sql = "SELECT keywords FROM user_data WHERE user_id = %s"
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
    sql = "UPDATE user_data SET keywords = %s, state = NULL WHERE user_id = %s"
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
    sql = "SELECT state FROM user_data WHERE user_id = %s"
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
    sql = "UPDATE user_data SET state = %s WHERE user_id = %s"
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
    sql = "SELECT user_id FROM user_data WHERE user_id = %s"
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
    sql = "INSERT INTO user_data (user_id) VALUES (%s)"
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
    for i, kw in enumerate(keywords):
        if i != 0:
            sql += " AND "
        sql += "post_content LIKE %s AND post_content NOT LIKE %s"  # 添加了一个过滤条件
    sql += ") ORDER BY post_time DESC LIMIT 20"  # 按照 post_time 遞減排序，並限制結果為最近的 20 筆

    # 獲取一周前的時間
    week_ago = datetime.now() - datetime.timedelta(weeks=1)
    week_ago_str = week_ago.strftime('%Y-%m-%d %H:%M:%S')

    # 執行 SQL 查詢
    cursor.execute(sql, (week_ago_str, ) + tuple(f"%{kw}%" for kw in keywords) + tuple("%求租%" for _ in keywords))

    results = cursor.fetchall()
    print(results)
    
    # 關閉連線
    cursor.close()
    conn.close()

    return results

# 讀取已紀錄的 post_id
def get_recorded_post_ids():
    try:
        with open("recorded_post_ids.txt", "r") as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()

# 寫入已紀錄的 post_id
def record_post_id(post_id):
    with open("recorded_post_ids.txt", "a") as file:
        file.write(post_id + "\n")

def fetch_and_insert_posts():
    group_post = []
    
    group1_id='464870710346711'
    group2_id='459966811445588'
    group3_id='189793166068662'
    #group4_id='464870710346711'
    #group5_id='464870710346711'
    
    recorded_post_ids = get_recorded_post_ids()

    print(f'记录看过的 post_id{recorded_post_ids}')

    for post in get_posts(group=group1_id, pages=1,cookies='cookies.txt'):
        post_id = post['post_id']
        
        if post_id in recorded_post_ids:
            print(f'已紀錄過的 post_id，略過處理')
            continue
        
        post_text = post['text']
        post_time = post['time']
        post_link = post['post_url']
        
        print(f'找到貼文了，貼文時間：{post_time}')
        
        post_data = {
            'post_text': post_text,
            'post_time': post_time,
            'post_link': post_link
        }
        group_post.append(post_data)
        record_post_id(post_id)
    
        time.sleep(10)
    
    print('第一個社團找完了~~~~~~~~~~~~~~~~~~~~')
    
    #------------------------------------
    for post in get_posts(group=group2_id, pages=1,cookies='cookies.txt'):
        post_id = post['post_id']
        
        if post_id in recorded_post_ids:
            print(f'已紀錄過的 post_id，略過處理')
            continue
        
        post_text = post['text']
        post_time = post['time']
        post_link = post['post_url']
        
        print(f'找到貼文了，貼文時間：{post_time}')
        
        post_data = {
            'post_text': post_text,
            'post_time': post_time,
            'post_link': post_link
        }
        group_post.append(post_data)
        record_post_id(post_id)
    
        time.sleep(10)
    
    print('第二個社團找完了~~~~~~~~~~~~~~~~~~~~')
    
    #------------------------------------
    for post in get_posts(group=group3_id, pages=1,cookies='cookies.txt'):
        post_id = post['post_id']
        
        if post_id in recorded_post_ids:
            print(f'已紀錄過的 post_id，略過處理')
            continue
        
        post_text = post['text']
        post_time = post['time']
        post_link = post['post_url']
        
        print(f'找到貼文了，貼文時間：{post_time}')
        
        post_data = {
            'post_text': post_text,
            'post_time': post_time,
            'post_link': post_link
        }
        group_post.append(post_data)
        record_post_id(post_id)
    
        time.sleep(10)
    
    print('第三個社團找完了~~~~~~~~~~~~~~~~~~~~')
    
    # 連接到資料庫
    db = mysql.connector.connect(**db_config)
    
    # 建立游標物件
    cursor = db.cursor()
    
    # 將資料插入資料庫
    for post_data in group_post:
        sql = "INSERT INTO post_data (post_content, post_time, post_link) VALUES (%s, %s, %s)"
        values = (post_data['post_text'], post_data['post_time'], post_data['post_link'])
        cursor.execute(sql, values)
    
    # 提交更改
    db.commit()
    
    # 關閉游標和資料庫連線
    cursor.close()
    db.close()
    
    print('-----------更新完成資料庫-----------')

@app.route('/trigger', methods=['POST'])
def start_trigger():
    while True:
        fetch_and_insert_posts()
        time.sleep(600)  # 每 30 分鐘執行一次
        return '觸發成功！'

#@app.route('/trigger', methods=['POST'])
#def trigger():
   # threading.Thread(target=start_trigger).start()
    #return '觸發成功！'

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
                                label='更新找房條件',
                                text='更新找房條件'
                            ),
                            MessageTemplateAction(
                                label='聯絡我們',
                                text='聯絡我們'
                            )   
                        ]
                        
                    )
                )
            )
        else:
            save_user_state(user_id, "首次輸入找房條件")  # 先儲存用戶的回傳訊息
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請輸入您的找房條件\n\n若要設定復數個關鍵字，請用,區隔\n\n⭐ 範例 1：大安區,套房\n⭐ 範例 2：文湖線,兩房\n⭐ 範例 3：南京復興站")
            )
    elif message == "更新找房條件":
        save_user_state(user_id, "更新找房條件")  # 先儲存用戶的回傳訊息

        # 再等待用戶的下一句回傳訊息
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入您的找房條件\n\n若要設定復數個關鍵字\n\n請用半形的逗號做區隔\n\n⭐ 範例 1：大安區,套房\n⭐ 範例 2：文湖線,兩房\n⭐ 範例 3：南京復興站")
        )
        
    elif message == "聯絡我們":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="如果您在使用的過程中有遇到任何異常，或是有什麼想對我們說的話\n\n您可以透過這個表單與我們聯繫\n\nhttps://docs.google.com/forms/d/e/1FAIpQLSfGW8O6O6mIM_dIe08Z53y4f45kHZbo_FRksoJfIkQxYugMjg/viewform\n\n如過這個服務真的有幫助到您的話，您可以透過這個連結贊助我們一杯咖啡，不然 Line 發訊息真的好貴啊 🥺\nhttps://bmc.link/poyu9090")
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
                       text=f'建議您更改關鍵字條件，太多關鍵字可能導致找不到完全符合的貼文',
                       actions=[
                           MessageTemplateAction(
                               label='開始找房',
                               text='開始找房'
                           ),
                           MessageTemplateAction(
                               label='更新找房條件',
                               text='更新找房條件'
                           ),
                           MessageTemplateAction(
                               label='聯絡我們',
                               text='聯絡我們'
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
           line_bot_api.push_message(
               user_id,
               TemplateSendMessage(
                   alt_text='Buttons template',
                   template=ButtonsTemplate(
                       title='已經搜尋完成',
                       text=f'已經回傳完符合關鍵字『{keywords}』的貼文囉！\n\n你可以過一段時間再搜尋一次，或是『更新找房條件』再『開始找房』',
                       actions=[
                           MessageTemplateAction(
                               label='開始找房',
                               text='開始找房'
                           ),
                           MessageTemplateAction(
                               label='更新找房條件',
                               text='更新找房條件'
                           ),
                           MessageTemplateAction(
                               label='聯絡我們',
                               text='聯絡我們'
                           )
                       ]
                   )
               )
           )     
    
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
                                label='更新找房條件',
                                text='更新找房條件'
                            ),
                            MessageTemplateAction(
                                label='聯絡我們',
                                text='聯絡我們'
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
                        text=f'設定完成！這是您目前設定的找房條件\n\n{message}\n\n可以開始找房囉！',
                        actions=[
                            MessageTemplateAction(
                                label='開始找房',
                                text='開始找房'
                            ),
                            MessageTemplateAction(
                                label='更新找房條件',
                                text='更新找房條件'
                            ),
                            MessageTemplateAction(
                                label='聯絡我們',
                                text='聯絡我們'
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
                        text='哈囉您好～\n\n您可以使用以下按鈕開始找房或是找租客的服務喔！\n\n我會每個小時內更新最新的台北租屋資訊！\n\n提醒您先點擊或輸入『更新找房條件』，設定完成後再點擊或輸入『開始找房』喔！',
                        actions=[
                            MessageTemplateAction(
                                label='更新找房條件',
                                text='更新找房條件'
                            ),   
                            MessageTemplateAction(
                                label='開始找房',
                                text='開始找房'
                            ),
                            MessageTemplateAction(
                                label='聯絡我們',
                                text='聯絡我們'
                            )                                  
                        ]
                    )
                )
            )

if __name__ == "__main__":
    app.run()
