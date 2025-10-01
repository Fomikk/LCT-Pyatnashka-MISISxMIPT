import os
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

print("FOLDER_ID:", os.getenv("YC_FOLDER_ID"))
print("API_KEY:", os.getenv("YC_API_KEY")[:6] + "...")
