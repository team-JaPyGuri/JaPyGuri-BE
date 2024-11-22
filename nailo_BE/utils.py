from .models import Customers, Shops
import logging

logger = logging.getLogger(__name__)

def get_user_id(user_type, user_id):
    """
    user_type과 user_id를 기반으로 (user객체, user_type) 튜플을 반환
    """
    try:
        if user_type == 'customer':
            user = Customers.objects.get(customer_id=user_id)
            logger.info(f"Found customer: {user_id}")
            return (user, 'customer')
        
        elif user_type == 'shop':
            user = Shops.objects.get(shop_id=user_id)
            logger.info(f"Found shop: {user_id}")
            return (user, 'shop')
        
        else:
            logger.error(f"Invalid user_type provided: {user_type}")
            return None, None
        
    except (Customers.DoesNotExist, Shops.DoesNotExist) as e:
        logger.error(f"User not found: {str(e)}")
        return None, None
    
    except Exception as e:
        logger.error(f"Unexpected error in get_user_id: {str(e)}")
        return None, None