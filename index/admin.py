from django.contrib import admin
from .models import User, Purchase, SalePrice, Transaction, Buyer

admin.site.register(User)
admin.site.register(Purchase)
admin.site.register(SalePrice)
admin.site.register(Transaction)
admin.site.register(Buyer)
