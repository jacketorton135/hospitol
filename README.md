
MR 蔣AI機器人 架構
![image](https://github.com/user-attachments/assets/fc0ebb42-b969-43c1-a9ff-6a51d10f30fd)



感謝您的訊息！

感謝您使用MR.蔣AI服務

輸入以下內容
圖表:{channel_id},{Write_key},{fieldxx}
帶入對應內容可以看到自己Thingspeak上的心跳圖表。
若輸入的使用者不存在會說User not found

範例內容
圖表:2466473,GROLYCVTU08JWN8Q,field1
可以看到別人的圖

ai:訊息 回應訊息

![image](https://github.com/user-attachments/assets/256873b5-1735-42e4-8c6c-985923598631)


![image](https://github.com/user-attachments/assets/f082ce52-332e-435d-9329-e7acb1f77420)




![image](https://img.ltn.com.tw/Upload/health/page/800/2022/05/14/3926479_1.jpg)](https://github.com/jacketorton135/proj_linebot/blob/main/images.jpg)

OpenAI 為預設了三種角色，分別是「系統（系統）」、「助理（助理）」以及「使用者（使用者）」。的回報。
ChatGPT 說：
針對該話行為和規則。​​​​​​這段程式的核心是利用 OpenAI 的 Chat Completion API 來建立一個針對會話系統，並根據不同角色來設定針對會話的執行和規則。和「使用者」這三種角色的解釋，並說明它們在程式中的作用和「使用者」這三種角色的解釋，並說明它們在程式中的作用。

角色解讀1.角色解決
使用OpenAI的ChatGPT模型時，有三種預設角色：

“系統”針對這個問題想法、規則和基礎。​​​​​​​​。。（系統角色）：這個角色用來設定針對故事的背景、規則和基準。

“用戶”該角色代表使用者的疑問或輸入問題。（使用者角色）： 使用者角色代表使用者的問答或輸入。使用者透過角色提出問答或表達需求，並根據人工智慧根據預設設定的時間表回饋。

“助手”機器人類對使用者的疑問提供答案。（助理角色）這個角色是人工智慧的回應角色，代表機器人員針對使用者的疑問提供答案。

程序中如何運作2.程序中如何運作
程呼叫中在我們的專案中，這些角色的運作存在於OpenAI的ChatCompletion.create呼叫中。

Python

複製
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",  # 使用的模型
    messages=[  # 這裡是聊天訊息的列表，包含 system、user 和 assistant 角色的訊息
        {"role": "system", "content": "你是一個醫療助手，專門回答關於心臟衰竭的問題。使用提供的心臟衰竭數據來回答問題。"},
        {"role": "user", "content": text}  # 這是來自使用者的訊息
    ],
    temperature=0.7,  # 創意程度設定，數值越高，回應的多樣性越大
    max_tokens=500  # 設定最大回應字數
)
系統角色（system）在這個程式中，系統角色用來設定整體的對情境和指揮AI的回應例如：​：
在這個過程中，系統角色用來設定整個系統的針對情境和指揮AI的反應邏輯。

Python

複製
{"role": "system", "content": "你是一個醫療助手，專門回答關於心臟衰竭的問題。使用提供的心臟衰竭數據來回答問題。"}
這個AI，無用戶問題什麼問題，都應該依 據心臟地帶執行相關的理由回答，並扮演一個醫療助手角色。

使用者角色（使用者）：
這是由使用者向機器發出詢問的部分text。

Python

複製
{"role": "user", "content": text}
該計劃旨在透過 GPT 模型實現對特定物件的訪問，從而實現對特定物件的存取。

助理角色（assistant）：助理角色代表機器人向
專案提供回報。systemuserresponse['choices'][0]['message']['content']

例如，根據使用者的需求，模型可能會產生一段回答，這段回答會以助理角色的形式傳回。

3.具體例子
假設備使用者提出了一個有關核心職能的問題：

Python

複製
query = "心臟衰竭的發病條件是什麼？"
系統角色：首先，系統角色設定針對的主題與規劃原則：

Python

複製
{"role": "system", "content": "你是一個醫療助手，專門回答關於心臟衰竭的問題。使用提供的心臟衰竭數據來回答問題。"}
使用者的角色：當然，使用者發出的問題：

Python

複製
{"role": "user", "content": "心臟衰竭的發病條件是什麼？"}
助理角色：根據這些輸入，AI會產生一個答案（例如）：

Python

複製
{"role": "assistant", "content": "心臟衰竭的發病條件包括：...（具體條件的列表）"}
4.為什麼我要使用這個角色？
清晰的物件結構：使用這些角色可以幫助模型更好地理解物件的背景，並可以根據上下文為其提供合適的回報。

靈活性：系統角色可以在對話過程中設定規則或改變對話的上下文，使AI的反應更靈敏地對應不同的情況。

一致性：透過在系統中設定明確的職責指令，可以保證模型的回答性，並且在每個情境下仍然能夠遵循預約原則和指導原則。

5.總結
在這個階段式中，角色「系統」、「使用者」和「助手」的角色是針對故事中的不同元素：

系統設定針對的概念和規則。

用戶提出疑問或需求。

助理提供回答。
