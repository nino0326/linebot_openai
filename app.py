from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import requests

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))

# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# Claude API Key
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')

def claude_response(text):
    # Claude API URL
    API_URL = "https://claude.anthropic.com/v1/complete"

    # 构建请求体
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CLAUDE_API_KEY}"
    }

    data = {
        "prompt": text,
        "max_tokens_to_sample": 500,
        "temperature": 0.5
    }

    # 发送请求
    response = requests.post(API_URL, headers=headers, json=data)

    # 检查请求是否成功
    if response.status_code == 200:
        # 获取响应数据
        result = response.json()
        answer = result["response"]
        return answer.strip(".")  # 去除句末句号
    else:
        # 处理错误
        error_message = f"Request failed with status code {response.status_code}"
        print(error_message)
        return error_message

# 监听所有来自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 处理消息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text

    try:
        claude_answer = claude_response(msg)
        print(claude_answer)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(claude_answer))
    except:
        print(traceback.format_exc())
        line_bot_api.reply_message(event.reply_token, TextSendMessage('Claude API调用出现错误,请检查日志'))

@handler.add(PostbackEvent)
def handle_message(event):
    print(event.postback.data)

@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
