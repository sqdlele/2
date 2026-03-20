from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from .models import Product, Category, Cart, CartItem, Wishlist, ProductImage
from .forms import CustomUserCreationForm, ProductForm, ProductImageFormSet


def home(request):
    """Главная страница"""
    categories = Category.objects.all()
    featured_products = Product.objects.filter(available=True)[:8]
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
    }
    return render(request, 'main/home.html', context)


def product_list(request):
    """Список товаров с фильтрацией и сортировкой"""
    products = Product.objects.filter(available=True).select_related('category')
    categories = Category.objects.all()
    
    # Фильтрация по категории
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    # Поиск
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Сортировка
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('name')
    
    # Пагинация
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_slug,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'main/product_list.html', context)


def product_detail(request, slug):
    """Детальная страница товара"""
    product = get_object_or_404(Product, slug=slug, available=True)
    images = product.images.all()
    related_products = Product.objects.filter(
        category=product.category, 
        available=True
    ).exclude(id=product.id)[:4]
    
    # Проверяем, есть ли товар в избранном
    in_wishlist = False
    if request.user.is_authenticated:
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        in_wishlist = wishlist.products.filter(id=product.id).exists()
    
    context = {
        'product': product,
        'images': images,
        'related_products': related_products,
        'in_wishlist': in_wishlist,
    }
    return render(request, 'main/product_detail.html', context)


def category_detail(request, slug):
    """Страница категории"""
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category, available=True)
    
    # Сортировка
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('name')
    
    # Пагинация
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'sort_by': sort_by,
    }
    return render(request, 'main/category_detail.html', context)


def register(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Аккаунт создан для {username}!')
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def cart_detail(request):
    """Страница корзины"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    context = {
        'cart': cart,
    }
    return render(request, 'main/cart_detail.html', context)


@login_required
@require_POST
def add_to_cart(request, product_id):
    """Добавление товара в корзину"""
    product = get_object_or_404(Product, id=product_id, available=True)
    cart, created = Cart.objects.get_or_create(user=request.user)

    if product.stock <= 0:
        messages.error(request, f'"{product.name}" нет в наличии')
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        if cart_item.quantity >= product.stock:
            messages.warning(request, f'Для "{product.name}" достигнут максимум по остатку ({product.stock} шт.)')
            return redirect(request.META.get('HTTP_REFERER', 'home'))
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f'{product.name} добавлен в корзину')
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
@require_POST
def update_cart_item(request, item_id):
    """Обновление количества товара в корзине"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        messages.error(request, 'Некорректное количество товара')
        return redirect('cart_detail')

    if quantity > 0:
        max_allowed = cart_item.product.stock
        if max_allowed <= 0:
            product_name = cart_item.product.name
            cart_item.delete()
            messages.warning(request, f'"{product_name}" больше нет в наличии и удален из корзины')
            return redirect('cart_detail')

        if quantity > max_allowed:
            quantity = max_allowed
            messages.warning(request, f'Количество ограничено остатком: {max_allowed} шт.')

        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, 'Количество товара обновлено')
    else:
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f'{product_name} удален из корзины')
    
    return redirect('cart_detail')


@login_required
@require_POST
def remove_from_cart(request, item_id):
    """Удаление товара из корзины"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    
    messages.success(request, f'{product_name} удален из корзины')
    return redirect('cart_detail')


@login_required
@require_POST
def toggle_wishlist(request, product_id):
    """Добавление/удаление товара из избранного"""
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    if wishlist.products.filter(id=product_id).exists():
        wishlist.products.remove(product)
        message = f'{product.name} удален из избранного'
    else:
        wishlist.products.add(product)
        message = f'{product.name} добавлен в избранное'
    
    messages.success(request, message)
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def wishlist_detail(request):
    """Страница избранного"""
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    context = {
        'wishlist': wishlist,
    }
    return render(request, 'main/wishlist_detail.html', context)


@login_required
def add_product(request):
    """Добавление нового товара (для администраторов)"""
    if not request.user.is_staff:
        messages.error(request, 'У вас нет прав для добавления товаров')
        return redirect('home')
    
    if request.method == 'POST':
        form = ProductForm(request.POST)
        formset = ProductImageFormSet(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            product = form.save()
            formset.instance = product
            formset.save()
            messages.success(request, f'Товар "{product.name}" успешно добавлен')
            return redirect('product_detail', slug=product.slug)
    else:
        form = ProductForm()
        formset = ProductImageFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Добавить товар'
    }
    return render(request, 'main/add_product.html', context)


@login_required
def edit_product(request, slug):
    """Редактирование товара (для администраторов)"""
    if not request.user.is_staff:
        messages.error(request, 'У вас нет прав для редактирования товаров')
        return redirect('home')
    
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        formset = ProductImageFormSet(request.POST, request.FILES, instance=product)
        
        if form.is_valid() and formset.is_valid():
            product = form.save()
            formset.save()
            messages.success(request, f'Товар "{product.name}" успешно обновлен')
            return redirect('product_detail', slug=product.slug)
    else:
        form = ProductForm(instance=product)
        formset = ProductImageFormSet(instance=product)
    
    context = {
        'form': form,
        'formset': formset,
        'product': product,
        'title': 'Редактировать товар'
    }
    return render(request, 'main/add_product.html', context)


@login_required
def delete_product(request, slug):
    """Удаление товара (для администраторов)"""
    if not request.user.is_staff:
        messages.error(request, 'У вас нет прав для удаления товаров')
        return redirect('home')
    
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Товар "{product_name}" успешно удален')
        return redirect('product_list')
    
    context = {
        'product': product,
    }
    return render(request, 'main/delete_product.html', context)