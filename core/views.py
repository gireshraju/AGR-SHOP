from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.db.models import Sum

from .forms import CustomUserCreationForm, ProductForm
from .models import Profile, Product, CartItem, Order, OrderItem

# Home View
def home(request):
    return render(request, 'core/home.html')

# Signup View
def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data['role']
            Profile.objects.create(user=user, role=role)
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/signup.html', {'form': form})

# Login View
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('products')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

# Product List View
def products(request):
    products = Product.objects.values('name').annotate(total_stock=Sum('stock'))
    product_details = []
    for product in products:
        product_info = Product.objects.filter(name=product['name']).first()
        product_details.append({
            'name': product['name'],
            'total_stock': product['total_stock'],
            'product_obj': product_info
        })
    cart_count = CartItem.objects.filter(user=request.user).count() if request.user.is_authenticated else 0
    return render(request, 'core/products.html', {'product_details': product_details, 'cart_count': cart_count})

# Product Detail View
@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_count = CartItem.objects.filter(user=request.user).count()
    return render(request, 'core/product_detail.html', {'product': product, 'cart_count': cart_count})

# Product Registration View (Seller Only)
@login_required
def register_product(request):
    # Ensure the user is a seller
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'seller':
        return redirect('products')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['name']
            stock = form.cleaned_data['stock']
            image = form.cleaned_data['image']
            price = form.cleaned_data['price']

            existing_product = Product.objects.filter(name__iexact=name).first()

            if existing_product:
                existing_product.stock += stock
                existing_product.save()
                messages.success(request, f'Stock updated! {stock} units added to existing product "{name}".')
            else:
                Product.objects.create(
                    name=name,
                    stock=stock,
                    image=image,
                    price=price
                )
                messages.success(request, 'New product has been registered successfully!')

            return redirect('products')
    else:
        form = ProductForm()

    products = Product.objects.all()
    return render(request, 'core/register_product.html', {'form': form, 'products': products})

# Add to Cart
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)

    if not created:
        if cart_item.quantity < product.stock:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f'{product.name} has been added to your cart!')
        else:
            messages.error(request, f'Not enough stock available for {product.name}.')
    else:
        messages.success(request, f'{product.name} has been added to your cart!')

    return redirect('product_detail', product_id=product.id)

# Remove from Cart
@login_required
def remove_from_cart(request, product_id):
    CartItem.objects.filter(user=request.user, product_id=product_id).delete()
    return redirect('cart')

# Cart View
@login_required
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.get_total_price() for item in cart_items)
    return render(request, 'core/cart.html', {'cart_items': cart_items, 'total': total})

# Place Order
@login_required
def place_order(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if cart_items:
        order = Order.objects.create(user=request.user)
        for item in cart_items:
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)
            
            # Update product stock
            item.product.stock -= item.quantity
            item.product.save()
        
        cart_items.delete()
        messages.success(request, 'Your order has been placed successfully!')
        return redirect('orders')
    messages.error(request, 'Your cart is empty! Please add items to the cart.')
    return redirect('cart')


# Orders View
@login_required
def orders(request):
    user_orders = Order.objects.filter(user=request.user)
    return render(request, 'core/orders.html', {'orders': user_orders})

# Delete Order
@require_POST
@login_required
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.delete()
    messages.success(request, "Order marked as received.")
    return redirect('orders')

# Superuser Check
def is_admin(user):
    return user.is_superuser

# Superuser: View All Users
@user_passes_test(is_admin)
def users_list(request):
    profiles = Profile.objects.select_related('user').all()
    return render(request, 'core/users.html', {'profiles': profiles})



# Superuser: Delete User
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    return redirect('users')

# Optional Additional Protection for User List View
@login_required
def users_view(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: Only superusers can view this page.")
    users = User.objects.all()
    return render(request, 'core/users.html', {'users': users})

# Remove Product View
@login_required
def remove_product(request, product_id):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'seller':
        messages.error(request, "You don't have permission to remove products.")
        return redirect('products')

    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, f'Product "{product.name}" has been removed successfully.')
    return redirect('products')
