from django.contrib import admin
from .models import Products

# Register your models here.
@admin.register(Products)
class ProductAdmin(admin.ModelAdmin):
  list_display = ('name','category','price','is_available')
  list_filter = ('category','is_available')
  search_fields = ('name','description','category')