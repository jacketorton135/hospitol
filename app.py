from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
import os
import openai
import traceback
from thingspeak import Thingspeak

# 創建 Flask 應用，設定靜態檔案的路徑和 URL 路徑
app = Flask(__name__, static_folder="./static", static_url_path="/static")
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

# 設定 LINE Bot 的 Channel Access Token，用於與 LINE 平台進行通信
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# 設定 LINE Bot 的 Channel Secret，用於驗證 LINE 平台的回調請求
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# 設定 OpenAI API Key，用於調用 OpenAI GPT 模型
openai.api_key = os.getenv('OPENAI_API_KEY')

# 授權用戶列表，包含可以使用圖表功能的用戶 ID
auth_user_list = ["U39b3f15d09b42fbd028e5689156a49e1"]
# 授權用戶 AI 功能列表，包含可以使用 AI 功能的用戶 ID
auth_user_ai_list = ["U39b3f15d09b42fbd028e5689156a49e1"]

# 儲存用戶對話歷史，以便進行持續對話
user_conversations = {}

# 模擬心臟衰竭相關數據
heart_failure_data = {
    "屬性資訊": [
        "年齡", "性別", "心臟病史", "高血壓", "糖尿病", "吸煙史", "肥胖"
    ],
    "發病條件": [
        "左心室射血分數 (LVEF) < 40%",
        "心臟超音波顯示左心室收縮功能異常",
        "B型利鈉肽 (BNP) > 100 pg/mL 或 NT-proBNP > 300 pg/mL",
        "胸部X光顯示肺部水腫或心臟擴大"
    ],
    "心臟病發病標準": [
        "胸痛持續超過20分鐘",
        "心電圖顯示ST段上升",
        "心肌酶學指標升高（如肌鈣蛋白、肌酸激酶）"
    ],
    "心臟衰竭標準": [
        "紐約心臟協會(NYHA)功能分級II級以上",
        "呼吸困難",
        "疲勞",
        "運動耐受性下降",
        "下肢水腫"
    ]
}

# 使用 OpenAI GPT 回應用戶的問題
def GPT_response(text):
    try:
        # 調用 OpenAI GPT 模型生成回答
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一個醫療助手，專門回答關於心臟衰竭的問題。使用提供的心臟衰竭數據來回答問題。"},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=500
        )
        # 獲取 GPT 模型的回答
        answer = response['choices'][0]['message']['content'].strip()
        return answer
    except Exception as e:
        print(f"GPT 回應錯誤: {e}")
        return "對不起，我無法處理你的請求。"

# 根據用戶的查詢處理心臟衰竭相關問題
def process_heart_failure_query(query):
    response = "根據心臟衰竭相關數據：\n\n"
    
    # 檢查查詢中是否包含「屬性」或「資訊」，如果有則返回相關屬性資訊
    if "屬性" in query or "資訊" in query:
        response += "相關屬性資訊包括：\n" + "\n".join(f"- {attr}" for attr in heart_failure_data["屬性資訊"])
    
    # 檢查查詢中是否包含「發病條件」或「心臟衰竭條件」，如果有則返回心臟衰竭的發病條件
    if "發病條件" in query or "心臟衰竭條件" in query:
        response += "\n\n心臟衰竭的發病條件包括：\n" + "\n".join(f"- {cond}" for cond in heart_failure_data["發病條件"])
    
    # 檢查查詢中是否包含「心臟病」和「標準」，如果有則返回心臟病發病標準
    if "心臟病" in query and "標準" in query:
        response += "\n\n心臟病發病標準：\n" + "\n".join(f"- {std}" for std in heart_failure_data["心臟病發病標準"])
    
    # 檢查查詢中是否包含「心臟衰竭標準」，如果有則返回心臟衰竭標準
    if "心臟衰竭標準" in query:
        response += "\n\n心臟衰竭標準：\n" + "\n".join(f"- {std}" for std in heart_failure_data["心臟衰竭標準"])
    
    return response

# 處理來自 LINE 的回調請求
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']  # 獲取請求的簽名
    body = request.get_data(as_text=True)  # 獲取請求的內容
    app.logger.info("Request body: " + body)  # 記錄請求內容
    try:
        handler.handle(body, signature)  # 處理回調請求
    except InvalidSignatureError:
        abort(400)  # 如果簽名無效，返回 400 錯誤
    return 'OK'

# 處理來自 LINE 的消息事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id  # 獲取發送消息的用戶 ID
    input_msg = event.message.text  # 獲取用戶發送的消息內容
    check = input_msg[:3].lower()  # 提取消息的前綴（檢查是什麼類型的請求）
    user_msg = input_msg[3:].strip()  # 獲取實際的消息內容（去掉前綴）

    # 檢查用戶是否在授權用戶列表中
    if user_id in auth_user_list:
        # 處理圖表請求
        if check == "圖表:":
            try:
                # 解析用戶發送的圖表請求
                parts = user_msg.split(',')
                if len(parts) != 3:
                    raise ValueError("輸入格式錯誤。請使用正確格式，例如: '圖表:2466473,GROLYCVTU08JWN8Q,field1'")
                
                channel_id, key, field = parts
                print("用戶 channel_id: ", channel_id, "Read_key: ", key, "Field: ", field)
                
                # 檢查 field 是否有效
                if field not in ['field1', 'field2', 'field3', 'field4', 'field5']:
                    raise ValueError("無效的 field 識別符。請使用 'field1', 'field2', 'field3', 'field4', 或 'field5'。")
                
                # 創建 Thingspeak 物件並處理圖表數據
                ts = Thingspeak()
                result = ts.process_and_upload_field(channel_id, key, field)
                
                # 根據處理結果返回相應的消息
                if result == 'Not Found':
                    message = TextSendMessage(text="數據未找到或無法處理請求。")
                elif result == 'Invalid Field':
                    message = TextSendMessage(text="無效的 field 識別符。請使用 'field1', 'field2', 'field3', 'field4', 或 'field5'。")
                else:
                    # 返回處理後的圖表圖片
                    image_path = result['image_path']
                    image_url = f"https://{request.host}/static/{os.path.basename(image_path)}"
                    image_message = ImageSendMessage(
                        original_content_url=image_url,
                        preview_image_url=image_url
                    )
                    line_bot_api.reply_message(event.reply_token, image_message)
            except Exception as e:
                print(f"處理圖表請求時錯誤: {e}")
                message = TextSendMessage(text=f"處理圖表請求時出現問題: {str(e)}")
                line_bot_api.reply_message(event.reply_token, message)
        
        # 處理 AI 請求
        elif check == 'ai:' and user_id in auth_user_ai_list:
            try:
                # 初始化用戶對話歷史
                if user_id not in user_conversations:
                    user_conversations[user_id] = ""

                # 更新用戶對話歷史
                user_conversations[user_id] += user_msg + " "

                # 根據用戶消息處理 AI 請求
                if "心臟衰竭" in user_msg:
                    response = process_heart_failure_query(user_msg)
                else:
                    response = GPT_response(user_conversations[user_id])

                print(response)

                # 更新用戶對話歷史
                user_conversations[user_id] += response + " "

                # 保持對話歷史長度在 2000 個字符以內
                if len(user_conversations[user_id]) > 2000:
                    user_conversations[user_id] = user_conversations[user_id][-2000:]

                # 回應用戶的消息
                line_bot_api.reply_message(event.reply_token, TextSendMessage(response))
            except Exception as e:
                print(f"GPT 回應錯誤: {e}")
                line_bot_api.reply_message(event.reply_token, TextSendMessage('對不起，我無法處理你的請求。'))

        # 處理結束對話請求
        elif check == 'end' and user_id in auth_user_ai_list:
            if user_id in user_conversations:
                del user_conversations[user_id]  # 刪除用戶的對話歷史
            line_bot_api.reply_message(event.reply_token, TextSendMessage('對話已結束。'))

    # 如果用戶不在授權列表中，回應無權限消息
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage('您沒有權限使用此功能。'))

# 處理回調事件
@handler.add(PostbackEvent)
def handle_postback(event):
    print(event.postback.data)  # 打印回調數據

# 處理新成員加入事件
@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id  # 獲取新加入成員的用戶 ID
    gid = event.source.group_id  # 獲取群組 ID
    profile = line_bot_api.get_group_member_profile(gid, uid)  # 獲取用戶資料
    name = profile.display_name  # 獲取用戶顯示名稱
    message = TextSendMessage(text=f'{name} 歡迎加入')  # 構建歡迎消息
    line_bot_api.reply_message(event.reply_token, message)  # 發送歡迎消息

# 主程序入口，啟動 Flask 應用
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))  # 獲取應用的埠號
    app.run(host='0.0.0.0', port=port)  # 啟動 Flask 應用
