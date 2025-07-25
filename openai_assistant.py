import openai

import config
from utils import get_thread_id_from_recipient_id, update_thread_id_from_recipient_id

openai.api_key = config.OPENAI_API_KEY


def ask_openai_assistant(query: str, recipient_id: str) -> str:
    try:
        # Lấy thread_id đã lưu nếu có
        thread_id = get_thread_id_from_recipient_id(recipient_id)
        print(thread_id)

        # Nếu chưa có thì tạo thread mới
        if thread_id:
            thread = openai.beta.threads.retrieve(
                thread_id=thread_id
                )
        else:
            thread = openai.beta.threads.create()
            update_thread_id_from_recipient_id(recipient_id, thread.id)

        print(thread.id)

        # Thêm message từ user vào thread
        _ = openai.beta.threads.messages.create(
            thread_id=thread.id,
            content=query,
            role='user'
        )

        # Tạo run với Assistant ID đã được cấu hình system prompt trên dashboard
        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=config.ASSISTANT_ID
        )

        print(run.id)
        flag = True

        # Đợi Assistant phản hồi xong
        while flag:
            retrieved_run = openai.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if retrieved_run.status == 'completed':
                flag = False

        # Lấy message mới nhất từ assistant
        retrieved_messages = openai.beta.threads.messages.list(
            thread_id=thread.id
            )
        print(retrieved_messages.data[0])
        message_text = retrieved_messages.data[0].content[0].text.value
        return message_text
    except:
        return config.ERROR_MESSAGE
