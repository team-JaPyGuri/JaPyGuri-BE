from rest_framework import serializers
from .models import *

class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shops
        fields = ['shop_key', 'shop_name', 'shop_id', 'lat', 'lng', 'shop_url']

class DesignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designs
        fields = fields = ['design_key', 'design_name', 'design_url', 'price', 'like_count', 'is_active']
        
class AddRequestSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)

    class Meta:
        model = Request
        fields = ['request_key', 'shop_name', 'status', 'price', 'contents']

# 샵 응답 목록 조회
class ResponseListSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)
    status = serializers.CharField(source='request.status', read_only=True)
    request_key = serializers.UUIDField(source='request.request_key', read_only=True)
    
    class Meta:
        model = Response
        fields = [
            'response_key',
            'request_key',
            'shop_name', 
            'price', 
            'contents', 
            'status',
        ]
        
class RequestSerializer(serializers.Serializer):
    design_key = serializers.UUIDField(required=True)
    customer_key = serializers.UUIDField(required=True)
    shop_key = serializers.UUIDField(required=True)
    contents = serializers.CharField(required=False, allow_blank=True, default='')

class ResponseSerializer(serializers.Serializer):
    request_key = serializers.UUIDField()
    status = serializers.ChoiceField(choices=['accepted', 'rejected'])
    price = serializers.IntegerField(required=False)
    contents = serializers.CharField(required=False, default='')