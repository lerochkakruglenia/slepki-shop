# app.py - точка входа для двух ботов
import os
import sys

# Определяем, какой бот запускать по переменной окружения
bot_type = os.environ.get('BOT_TYPE', 'client')

if bot_type == 'admin':
    import admin
else:
    import client