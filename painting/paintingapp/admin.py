from django.contrib import admin
from .models import Category, Product, Artist, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'artist', 'price', 'stock', 'created_at')
    list_filter = ('category', 'artist', 'stock')
    search_fields = ('name', 'description', 'artist__name')
    raw_id_fields = ('artist',)

@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'profession', 'user')
    search_fields = ('name', 'profession', 'bio')
    raw_id_fields = ('user',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ('product',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email')
    inlines = [OrderItemInline]
    raw_id_fields = ('user',)
