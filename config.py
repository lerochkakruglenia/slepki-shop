import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_TOKEN = os.getenv('CLIENT_TOKEN')
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()]