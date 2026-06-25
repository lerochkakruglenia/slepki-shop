from supabase import create_client
import config
import random


class Database:
    def __init__(self):
        self.client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

    # ===== ЗАКАЗЫ =====
    def create_order(self, data):
        data['order_number'] = f"SL-{random.randint(1000, 9999)}"
        response = self.client.table('orders').insert(data).execute()
        return response.data[0] if response.data else None

    def get_all_orders(self):
        response = self.client.table('orders').select('*').order('created_at', desc=True).execute()
        return response.data

    def get_new_orders(self):
        response = self.client.table('orders').select('*').eq('status', 'new').order('created_at', desc=True).execute()
        return response.data

    def get_orders_by_user(self, telegram_id):
        response = self.client.table('orders').select('*').eq('client_telegram_id', str(telegram_id)).order(
            'created_at', desc=True).execute()
        return response.data

    def update_status(self, order_id, status, completion_date=None):
        data = {'status': status} if status else {}
        if completion_date:
            data['completion_date'] = completion_date
        if data:
            response = self.client.table('orders').update(data).eq('id', order_id).execute()
            return response.data[0] if response.data else None
        return None

    # ===== ОТЗЫВЫ =====
    def create_review(self, data):
        response = self.client.table('reviews').insert(data).execute()
        return response.data[0] if response.data else None

    def get_approved_reviews(self):
        response = self.client.table('reviews').select('*').eq('is_approved', True).order('created_at',
                                                                                          desc=True).limit(10).execute()
        return response.data

    def get_pending_reviews(self):
        response = self.client.table('reviews').select('*').eq('is_approved', False).order('created_at',
                                                                                           desc=True).execute()
        return response.data

    def approve_review(self, review_id):
        response = self.client.table('reviews').update({'is_approved': True}).eq('id', review_id).execute()
        return response.data[0] if response.data else None

    def delete_review(self, review_id):
        response = self.client.table('reviews').delete().eq('id', review_id).execute()
        return response.data


db = Database()
