from django.urls import path
from . import views

urlpatterns = [
    # Home Page
    path('', views.home, name='home'),

    # Signup and Login
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),

    # Users and User Management (Superuser only)
    path('users/', views.users_view, name='users_view'),  # Renamed 'users' to 'users_view'
    path('users/list/', views.users_list, name='users_list'),  # Renamed 'users' to 'users_list'
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),

    # Product Views
    path('products/', views.products, name='products'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    # Cart Views
    path('cart/', views.cart, name='cart'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),

    # Order Views
    path('place_order/', views.place_order, name='place_order'),
    path('orders/', views.orders, name='orders'),
    path('orders/delete/<int:order_id>/', views.delete_order, name='delete_order'),

    # Product Registration for Sellers
    path('register-product/', views.register_product, name='register_product'),

    # Remove Product for Seller
    path('remove-product/<int:product_id>/', views.remove_product, name='remove_product'),
]
