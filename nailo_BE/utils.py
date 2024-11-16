from .models import Customers, Shops

def get_user_id(user_type, user_id):
    """
    user_type과 user_id를 기반으로 (user객체, user_type) 튜플을 반환
    """
    try:
        if user_type == 'customer':
            user = Customers.objects.get(customer_id=user_id)
            return (user, 'customer') 
        elif user_type == 'shop':
            user = Shops.objects.get(shop_id=user_id)
            return (user, 'shop')  
    except (Customers.DoesNotExist, Shops.DoesNotExist):
        return None, None 