from datetime import datetime
import threading
import time
import random

from flask import Flask, request

from openai_assistant import ask_openai_assistant
import config
from utils import is_office_hours, load_keywords, match_intent, log_message, INTENT_LOOKUP
from fb_graph_api import send_message_to_fb_messenger, send_text_message, send_quick_reply, send_button_message
from config import ZALO_OA_LINK, HOTLINE, REPLY_TIMEOUT_SECONDS


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def home():
    return 'OK', 200


@app.route('/facebook', methods=['GET'])
def facebook_get():
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        print(config.VERIFY_TOKEN)
        try:
            if mode == 'subscribe' and token == config.VERIFY_TOKEN:
                print('✅ WEBHOOK_VERIFIED')
                return challenge
            else:
                return 403
        except:
            return 403
        
        
def call_ask_openai_assistant_and_send_message_to_fb_messenger(query: str, recipient_id: str) -> str:
    try:
        handle_message(sender_id=recipient_id, message_text=query)
        
        message_text = ask_openai_assistant(query, recipient_id)
        message_text = f"[Trợ lý ảo của Sao Mai]: {message_text}"

        # Nếu message gần nhất có chứa từ liên hệ thì gửi nút
        #last_message = user_last_message.get(recipient_id, "")
        if any(x in message_text.lower() for x in ["liên hệ", "zalo", "hotline", "gửi thông tin", "kết nối"]):
            send_button_message(
                recipient_id=recipient_id,
                text="🔗 Anh/chị có thể liên hệ nhanh với Sao Mai qua các kênh sau để được hỗ trợ cụ thể hơn ạ:",
                zalo_url=ZALO_OA_LINK,
                hotline=HOTLINE
            )

    except Exception as e:
        print("❌ Lỗi:", e)
        send_message_to_fb_messenger(
            recipient_id,
            "🛠 Xin lỗi, hệ thống đang bận. Anh/chị vui lòng nhắn lại sau ít phút nhé!"
        )



    
    
@app.route('/facebook', methods=['POST'])
def facebook_post():
    #try:
      #  print('A new Facebook Messenger request...')
      #  body = request.get_json()
     #   recipient_id = body['entry'][0]['messaging'][0]['sender']['id']
      #  query = body['entry'][0]['messaging'][0]['message']['text']
      #  print(query)
       # print(recipient_id)
       # threading.Thread(target=call_ask_openai_assistant_and_send_message_to_fb_messenger,
        #                 args=(query, recipient_id)).start()
       # print('Request success.')
    #except:
     #   print('Request failed.')
      #  pass
    #return 'OK', 200
    try:
        print('A new Facebook Messenger request...')
        body = request.get_json()
        messaging_event = body['entry'][0]['messaging'][0]
        recipient_id = messaging_event['sender']['id']

        # Nếu là quick reply
        if 'message' in messaging_event and 'quick_reply' in messaging_event['message']:
                
            payload = messaging_event['message']['quick_reply']['payload']
            print("🔁 QUICK REPLY PAYLOAD:", payload)

            # Nếu payload có trong từ khóa → xử lý như bình thường
            if match_intent(payload, KEYWORDS):
                threading.Thread(
                    target=handle_message,
                    args=(recipient_id, payload),
                    kwargs={"quick_reply_payload": payload}
                ).start()
            elif 'message' in messaging_event and 'text' in messaging_event['message']:
                query = messaging_event['message']['text']
                print("💬 USER MESSAGE:", query)

                # 👉 Gọi handle_message trước, để xử lý logic chào hỏi + quick reply
                threading.Thread(
                    target=handle_message,
                    args=(recipient_id, query)
                ).start()



    except Exception as e:
        print('❌ Request failed:', e)

    return 'OK', 200







# Load từ khóa
KEYWORDS = load_keywords()


# Theo dõi người dùng
greeted_users = set()
pending_users = {}
user_last_message_time = {}
recent_users = {}
REPLY_COOLDOWN = 5  # thời gian chờ giữa 2 lần phản hồi


# -------------------------------
# XỬ LÝ TIN NHẮN KHÁCH GỬI
# -------------------------------
def handle_message(sender_id: str, message_text: str, quick_reply_payload: str = None):
    log_message(sender_id, message_text)
    now = time.time()
    #last_time = recent_users.get(sender_id, 0)


    #if now - last_time < REPLY_COOLDOWN:
     #   print(f"⏳ Gửi gần đây → bỏ qua")
      #  return


    recent_users[sender_id] = now
    user_last_message_time[sender_id] = now
    is_office = is_office_hours()


    if sender_id not in greeted_users:
        greeted_users.add(sender_id)
        if is_office:
            send_text_message(sender_id,
                "🌟 Em chào anh/chị ạ! Cảm ơn anh/chị đã nhắn tin cho Tập đoàn Cung ứng Nhân lực Sao Mai.\n"
            )
        else:
            send_text_message(sender_id,
                "🌟 Em chào anh/chị ạ! Cảm ơn anh/chị đã liên hệ với Tập đoàn Cung ứng Nhân lực Sao Mai.\n"
                "Hiện tại là *ngoài giờ hành chính* (8h–17h, Thứ 2–Thứ 6) nên chưa có nhân viên trực tiếp hỗ trợ mình.\n"
                "Nhưng không sao, em là *trợ lý ảo của Sao Mai*, em sẽ hỗ trợ anh/chị ngay bây giờ ạ!"
            )
            send_quick_reply(
                sender_id,
                "✨ Anh/chị đang quan tâm đến chương trình nào ạ?",
                ["XKLĐ Nhật Bản 🇯🇵", "XKLĐ Đài Loan 🇹🇼", "Du học Đài Loan 🎓", "Kết nối Zalo 💬"]
            )
            return


    if is_office:
        handle_during_working_hours(sender_id, now)
        
    if quick_reply_payload:
        handle_quick_reply(sender_id, quick_reply_payload)
        return
    
    # Nếu muốn xử lý chậm (chỉ khi không gọi ở nơi khác)
    else:
        threading.Thread(
            target=delayed_response,
            args=(sender_id, message_text, now)
        ).start()


   
def delayed_response(sender_id: str, message_text: str, message_time: float):
    time.sleep(35)  # chờ khoảng 30–60s


    # Nếu khách đã nhắn tiếp sau khi sleep → hủy phản hồi
    if user_last_message_time.get(sender_id, 0) > message_time:
        print("✋ Khách vừa nhắn tiếp → hủy trả lời")
        return


    # B1: Ưu tiên kiểm tra theo từ khóa
    intent = match_intent(message_text, KEYWORDS)


    if intent:
        response = intent["response"]
        if isinstance(response, list):
            response = random.choice(response)
        send_text_message(sender_id, response)
        return



    # B2: Nếu không khớp từ khóa → gửi GPT
    message_text = ask_openai_assistant(message_text, sender_id)
    send_text_message(sender_id, f"[Trợ lý ảo của Sao Mai]: {message_text}")



   
# -------------------------------
# TRONG GIờ HÀNH CHÍNH: CHỜ 5 PHÚt
# -------------------------------
def handle_during_working_hours(sender_id: str, message_time: float):
    send_text_message(
        sender_id,
        "🕒 Hiện tại anh/chị đang nhắn tin *trong giờ hành chính*, em đã báo cho bộ phận tư vấn, nhân viên tư vấn sẽ phản hồi trong ít phút. Mình vui lòng đợi chút nha! 😊"
    )


    if sender_id in pending_users:
        return


    def wait_and_handle():
        time.sleep(REPLY_TIMEOUT_SECONDS)
        if user_last_message_time.get(sender_id, 0) > message_time:
            return


        send_text_message(sender_id,
            "🤖 Dạ nhân viên chưa kịp phản hồi ạ. Em là *trợ lý ảo Sao Mai*, xin phép hỗ trợ trước nhé!"
        )
        send_quick_reply(
            sender_id,
            "✨ Anh/chị muốn tìm hiểu chương trình nào ạ?",
            ["XKLĐ Nhật Bản 🇯🇵", "XKLĐ Đài Loan 🇹🇼", "Du học Đài Loan 🎓", "Kết nối Zalo 💬"]
        )
        return


    pending_users[sender_id] = True
    threading.Thread(target=wait_and_handle).start()


# -------------------------------
# QUICK REPLY
# -------------------------------
def handle_quick_reply(sender_id: str, payload: str):
    if payload == "XKLĐ Nhật Bản 🇯🇵":
        send_text_message(sender_id,
            "🇯🇵 *XKLĐ Nhật Bản* thu nhập *26–35 triệu/tháng*.\n"
            "✅ Chi phí minh bạch, đào tạo bài bản, đơn hàng liên tục.\n"
        )
        send_quick_reply(
            sender_id,
            "✨ Anh/chị muốn biết thêm về phần nào ạ?",
            ["Chi phí đi Nhật", "Hồ sơ đi Nhật", "Quy trình đi Nhật"]
        )
        return


    elif payload == "XKLĐ Đài Loan 🇹🇼":
        send_text_message(sender_id,
            "🇹🇼 *XKLĐ Đài Loan* chi phí thấp, xuất cảnh nhanh, thu nhập *18–25 triệu/tháng*.\n"
        )
        send_quick_reply(
            sender_id,
            "✨ Anh/chị muốn biết thêm về phần nào ạ?",
            ["Chi phí đi Đài Loan", "Hồ sơ đi Đài Loan", "Thời gian xuất cảnh"]
        )
        return


    elif payload == "Du học Đài Loan 🎓":
        send_text_message(sender_id,
            "🎓 *Du học Đài Loan*  với chi phí hợp lý, bằng cấp quốc tế, có cơ hội làm thêm.\nGồm 2 hệ chính: *Du học hệ INTENSE* và *Du học hệ 1+4*.\n"
            "✨ Anh/chị muốn tìm hiểu hệ nào ạ?"
        )
        send_quick_reply(
            sender_id,
            "Vui lòng chọn hệ du học để em tư vấn kỹ hơn ạ:",
            ["Hệ INTENSE", "Hệ 1+4"]
        )
        return


    elif payload == "Hệ INTENSE":
        send_text_message(sender_id,
            "📘 *Du học hệ INTENSE* phù hợp với học sinh muốn vừa học vừa làm, chi phí thấp, được hỗ trợ học bổng và việc làm thêm.\n"
            "Thời gian học: 1 năm tiếng + 4 năm chuyên ngành."
        )
        send_quick_reply(
            sender_id,
            "✨ Anh/chị quan tâm điều gì nhất ạ?",
            ["Điều kiện du học", "Học phí", "Ngành học phổ biến"]
        )
        return


    elif payload == "Hệ 1+4":
        send_text_message(sender_id,
            "📗 *Du học hệ 1+4* yêu cầu có bằng THPT, học 1 năm tiếng rồi vào đại học 4 năm.\n"
            "Cơ hội định cư, chuyển tiếp sang nước thứ ba rất cao nếu học tốt."
        )
        send_quick_reply(
            sender_id,
            "✨ Anh/chị quan tâm điều gì nhất ạ?",
            ["Điều kiện du học", "Học phí", "Ngành học phổ biến"]
        )
        return


    elif payload == "Kết nối Zalo 💬":
        send_button_message(
            recipient_id=sender_id,
            text="🔗 Mình có thể kết nối nhanh với bên em bằng các cách sau, anh/chị chọn giúp em ạ:",
            zalo_url=ZALO_OA_LINK,
            hotline=HOTLINE,
            extra_button={
                "type": "web_url",
                "url": "https://saomaixkld.vn/",
                "title": "📋 Xem đơn hàng"
            }
        )
        return


    else:
        # Không khớp với bất kỳ quick reply cụ thể nào → fallback: từ khóa hoặc GPT
        intent_data = match_intent(payload, KEYWORDS)
        if intent_data:
            response = intent_data["response"]
            if isinstance(response, list):
                response = random.choice(response)
            send_text_message(sender_id, f"[Trợ lý ảo của Sao Mai]: {response}")
        else:
            now = time.time()
            user_last_message_time[sender_id] = now
            threading.Thread(
                target=delayed_response,
                args=(sender_id, payload, now)
            ).start()







