from rest_framework import serializers
from .models import Shops, Request, Response, Designs, Customers

class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shops
        fields = ['shopper_key', 'shopper_name', 'lat', 'lng']

class RequestSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='shop.shopper_name', read_only=True)

    class Meta:
        model = Request
        fields = ['request_key', 'shop_name', 'status', 'price', 'contents']

class ResponseSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='shop.shopper_name', read_only=True)
    status = serializers.CharField(source='request.status', read_only=True)

    class Meta:
        model = Response
        fields = ['response_key', 'shop_name', 'price', 'contents', 'status']

class ServiceRequestInputSerializer(serializers.Serializer):
    design_key = serializers.UUIDField()
    customer_key = serializers.UUIDField()
    contents = serializers.CharField(required=False, default='')

class ServiceResponseInputSerializer(serializers.Serializer):
    request_key = serializers.UUIDField()
    response = serializers.ChoiceField(choices=['accepted', 'rejected'])
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    contents = serializers.CharField(required=False, default='')