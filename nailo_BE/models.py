from django.db import models
from django.contrib.auth.models import User

class Shops(models.Model):
    shopper_key = models.CharField(max_length=255)
    shopper_id = models.CharField(max_length=255)
    shopper_name = models.CharField(max_length=255)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lng = models.DecimalField(max_digits=9, decimal_places=6) 
    created_at = models.DateTimeField(auto_now_add=True)
    intro_image = models.CharField(max_length=255)

    def __str__(self):
        return self.shopper_name


class Customers(models.Model):
    customer_key = models.CharField(max_length=255, primary_key=True)  
    customer_id = models.CharField(max_length=255, unique=True)        
    customer_pw = models.CharField(max_length=255)                    
    customer_name = models.CharField(max_length=255)                   
    created_at = models.DateTimeField(auto_now_add=True)               
    generated_image = models.URLField(max_length=500, blank=True, null=True)                  
    design_book = models.JSONField(blank=True, null=True)              

    def __str__(self):
        return self.customer_name

class Designs(models.Model):
    design_key = models.CharField(max_length=255, primary_key=True)       
    shopper_name = models.ForeignKey('Shops', on_delete=models.CASCADE) 
    design_name = models.CharField(max_length=255)                        
    price = models.IntegerField()                                         
    created_at = models.DateTimeField(auto_now_add=True)                 
    design_image = models.URLField(max_length=500, blank=True, null=True)                                                
    is_active = models.BooleanField(default=True)                         

    def __str__(self):
        return self.design_name

class Request(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    request_key = models.CharField(max_length=255, primary_key=True)  
    customer_key = models.ForeignKey('Customers', on_delete=models.CASCADE, related_name="requests")
    shopper_key = models.ForeignKey('Shops', on_delete=models.CASCADE, related_name="requests")
    design_key = models.ForeignKey('Designs', on_delete=models.CASCADE, related_name="requests")
    price = models.IntegerField() 
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    contents = models.TextField(blank=True, null=True)  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request {self.request_key} from {self.customer_key} for {self.design_key}"

class Response(models.Model):
    response_key = models.CharField(max_length=255, primary_key=True)     
    customer_key = models.ForeignKey('Customers', on_delete=models.CASCADE)  
    shopper_key = models.ForeignKey('Shops', on_delete=models.CASCADE)   
    request_key = models.ForeignKey('Request', on_delete=models.CASCADE)  
    price = models.CharField(max_length=255) # 네일숍에서 새로 입력                           
    contents = models.TextField(blank=True, null=True)            
    created_at = models.DateTimeField(auto_now_add=True)                    

    def __str__(self):
        return f"Response {self.response_key} to Request {self.request_key}"