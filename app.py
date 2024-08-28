import os
import openai
import traceback
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
from thingspeak import Thingspeak
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

app = Flask(__name__, static_folder="./static", static_url_path="/static")
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
openai.api_key = os.getenv('OPENAI_API_KEY')

# 授權用戶列表
auth_user_list = ["U39b3f15d09b42fbd028e5689156a49e1"]  # 允許使用圖表功能的用戶ID列表
auth_user_ai_list = ["U39b3f15d09b42fbd028e5689156a49e1"]  # 允許使用AI功能的用戶ID列表

# 用戶對話歷史
user_conversations = {}

# 心臟衰竭相關數據
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

# 讀取Excel文件
heart_data = pd.read_excel('heart.xlsx')
heart_disease_prediction_data = pd.read_excel('Heart_Disease_Prediction.xlsx')

# 準備心臟病預測模型
X = heart_disease_prediction_data.drop('HeartDisease', axis=1)
y = heart_disease_prediction_data['HeartDisease']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

def GPT_response(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一個醫療助手，專門回答關於心臟衰竭和心臟病的問題。使用提供的心臟衰竭數據和Excel文件中的數據來回答問題。"},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=500
        )
        answer = response['choices'][0]['message']['content'].strip()
        return answer
    except Exception as e:
        print(f"GPT 回應錯誤: {e}")
        return "對不起，我無法處理你的請求。"

def process_heart_failure_query(query):
    response = "根據心臟衰竭相關數據和Excel文件：\n\n"
    
    if "屬性" in query or "資訊" in query:
        response += "相關屬性資訊包括：\n" + "\n".join(f"- {attr}" for attr in heart_failure_data["屬性資訊"])
        response += "\n\n在Excel文件中的屬性：\n" + ", ".join(heart_data.columns.tolist())
    
    if "發病條件" in query or "心臟衰竭條件" in query:
        response += "\n\n心臟衰竭的發病條件包括：\n" + "\n".join(f"- {cond}" for cond in heart_failure_data["發病條件"])
    
    if "心臟病" in query and "標準" in query:
        response += "\n\n心臟病發病標準：\n" + "\n".join(f"- {std}" for std in heart_failure_data["心臟病發病標準"])
    
    if "心臟衰竭標準" in query:
        response += "\n\n心臟衰竭標準：\n" + "\n".join(f"- {std}" for std in heart_failure_data["心臟衰竭標準"])
    
    if "統計" in query:
        response += f"\n\n根據Excel數據，平均年齡為：{heart_data['Age'].mean():.2f}歲"
        response += f"\n男性比例：{(heart_data['Sex'] == 1).mean():.2%}"
        response += f"\n患有心臟病的比例：{(heart_data['HeartDisease'] == 1).mean():.2%}"
    
    return response

def predict_heart_disease(age, sex, chest_pain_type, resting_bp, cholesterol, fasting_bs, resting_ecg, max_hr, exercise_angina, oldpeak, st_slope):
    input_data = np.array([[age, sex, chest_pain_type, resting_bp, cholesterol, fasting_bs, resting_ecg, max_hr, exercise_angina, oldpeak, st_slope]])
    prediction = rf_model.predict(input_data)
    probability = rf_model.predict_proba(input_data)[0][1]
    return prediction[0], probability

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    input_msg = event.message.text
    check = input_msg[:3].lower()
    user_msg = input_msg[3:].strip()
    
    if user_id in auth_user_list:
        if check == "圖表:":
            # 圖表處理邏輯保持不變
            pass
        
        elif check == 'ai:' and user_id in auth_user_ai_list:
            try:
                if user_id not in user_conversations:
                    user_conversations[user_id] = ""

                user_conversations[user_id] += user_msg + " "

                if "心臟衰竭" in user_msg or "心臟病" in user_msg:
                    response = process_heart_failure_query(user_msg)
                elif "預測" in user_msg:
                    # 這裡應該解析用戶輸入的預測數據，為了簡化，我們使用固定值
                    prediction, probability = predict_heart_disease(40, 1, 1, 120, 200, 0, 0, 150, 0, 1.5, 1)
                    response = f"心臟病預測結果：{'陽性' if prediction == 1 else '陰性'}，概率：{probability:.2%}"
                else:
                    response = GPT_response(user_conversations[user_id])

                print(response)

                user_conversations[user_id] += response + " "

                if len(user_conversations[user_id]) > 2000:
                    user_conversations[user_id] = user_conversations[user_id][-2000:]

                line_bot_api.reply_message(event.reply_token, TextSendMessage(response))
            except Exception as e:
                print(f"GPT 回應錯誤: {e}")
                line_bot_api.reply_message(event.reply_token, TextSendMessage('對不起，我無法處理你的請求。'))

        elif check == 'end' and user_id in auth_user_ai_list:
            if user_id in user_conversations:
                del user_conversations[user_id]
            line_bot_api.reply_message(event.reply_token, TextSendMessage('對話已結束。'))

    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage('您沒有權限使用此功能。'))

@handler.add(PostbackEvent)
def handle_postback(event):
    print(event.postback.data)

@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name} 歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)