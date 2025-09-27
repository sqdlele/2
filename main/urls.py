from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('register/', views.register, name='register'),
    
    # Корзина
    path('cart/', views.cart_detail, name='cart_detail'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    # Избранное
    path('wishlist/', views.wishlist_detail, name='wishlist_detail'),
    path('toggle-wishlist/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    
    # Управление товарами (для администраторов)
    path('add-product/', views.add_product, name='add_product'),
    path('edit-product/<slug:slug>/', views.edit_product, name='edit_product'),
    path('delete-product/<slug:slug>/', views.delete_product, name='delete_product'),
]