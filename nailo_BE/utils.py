from .models import Customers, Shops

def get_user_id(user_type, user_id):
    """
    user_type과 user_id를 기반으로 Customer 또는 Shop 객체를 반환
    """
    try:
        if user_type == 'customer':
            return Customers.objects.get(customer_id=user_id)
        elif user_type == 'shop':
            return Shops.objects.get(shop_id=user_id)
    except (Customers.DoesNotExist, Shops.DoesNotExist):
        return None