import os

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ASSISTANT_ID = os.getenv('ASSISTANT_ID')

FB_PAGE_ACCESS_TOKEN = os.getenv('FB_PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')

ZALO_OA_LINK = os.getenv("ZALO_OA_LINK", "https://zalo.me/saomaihr0931446688")
HOTLINE = os.getenv("HOTLINE", "0931446688")


WORK_HOUR_START = os.getenv("WORK_HOUR_START", "08:00")
WORK_HOUR_END = os.getenv("WORK_HOUR_END", "17:00")
WORK_DAYS = list(map(int, os.getenv("WORK_DAYS", "0,1,2,3,4").split(",")))


REPLY_TIMEOUT_SECONDS = int(os.getenv("REPLY_TIMEOUT_SECONDS", 300))

ERROR_MESSAGE = 'We are facing an issue at this moment, please try after sometime.'

MAPPINGS_data = {"mappings": {}}