import uuid
from django.db import models
from django.contrib.auth.models import User

class Shops(models.Model):
    shop_key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    shop_id = models.CharField(max_length=255)
    shop_name = models.CharField(max_length=255)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lng = models.DecimalField(max_digits=9, decimal_places=6) 
    created_at = models.DateTimeField(auto_now_add=True)
    shop_url = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.shop_name

class Customers(models.Model):
    customer_key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)    
    customer_id = models.CharField(max_length=255, unique=True)                         
    customer_name = models.CharField(max_length=255)                   
    created_at = models.DateTimeField(auto_now_add=True)               
    generated_image = models.URLField(max_length=500, blank=True, null=True)                  

    def __str__(self):
        return self.customer_name

class Designs(models.Model):
    design_key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)    
    shop = models.ForeignKey(Shops, to_field='shop_key', on_delete=models.PROTECT) 
    design_name = models.CharField(max_length=255)                        
    price = models.IntegerField()                                         
    created_at = models.DateTimeField(auto_now_add=True)                 
    design_url = models.URLField(max_length=500, blank=True, null=True)
    like_count = models.IntegerField(null=True)
    tag = models.CharField(max_length=50, blank=True, null=True)                                         
    is_active = models.BooleanField(default=True)                         

    def __str__(self):
        return self.design_name

class Like(models.Model):
    customer = models.ForeignKey('Customers', on_delete=models.CASCADE, related_name="like")
    design = models.ForeignKey('Designs', on_delete=models.CASCADE, related_name="liked_design")
    liked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('customer', 'design')
        
class Request(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    request_key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    customer = models.ForeignKey('Customers', on_delete=models.CASCADE, related_name="requests")
    shop = models.ForeignKey(Shops, to_field='shop_key', on_delete=models.CASCADE, related_name="requests")
    design = models.ForeignKey('Designs', on_delete=models.CASCADE, related_name="requests")
    price = models.IntegerField() 
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    contents = models.TextField(blank=True, null=True)  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request {self.request_key} from {self.customer} for {self.design}"

class Response(models.Model):
    response_key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    customer = models.ForeignKey('Customers', on_delete=models.CASCADE, related_name="response")
    shop = models.ForeignKey(Shops, to_field='shop_key', on_delete=models.CASCADE, related_name="response")
    request = models.ForeignKey('Request', on_delete=models.CASCADE)  
    price = models.IntegerField() # 네일숍에서 새로 입력                           
    contents = models.TextField(blank=True, null=True)            
    created_at = models.DateTimeField(auto_now_add=True)                    

    def __str__(self):
        return f"Response {self.response_key} to Request {self.request}"
    
class TryOnHistory(models.Model):
    user = models.ForeignKey(Customers, on_delete=models.CASCADE)
    original_image = models.ImageField(upload_to='tryon/original/')
    predicted_image = models.ImageField(upload_to='tryon/predicted/')
    created_at = models.DateTimeField(auto_now_add=True)
    design_key = models.ForeignKey(Designs, to_field='design_key', on_delete=models.CASCADE)
    
    def __str__(self):
        return f"History for {self.user.customer_name} at {self.created_at}"