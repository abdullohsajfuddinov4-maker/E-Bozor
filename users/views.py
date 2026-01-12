from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .forms import SignupForm, UpdateProfileForm
from .models import CustomUser, Saved, Reminder, Transaction, Order
from products.models import Product
from decimal import Decimal

class SignupView(UserPassesTestMixin, View):
    def get(self, request):
        return render(
            request,
            'registration/signup.html',
            {'form': SignupForm()}
        )

    def post(self, request):
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account is successfully created.')
            return redirect('login')
        return render(
            request,
            'registration/signup.html',
            {'form': form}
        )

    def test_func(self):
        return not self.request.user.is_authenticated

def logout_view(request):
    logout(request)
    return redirect('/')


@login_required
def profile_view(request, username):
    # Получаем пользователя, чей профиль открыт
    owner = get_object_or_404(CustomUser, username=username)

    reminders = []
    # Загружаем напоминания только если это личный профиль
    if request.user == owner:
        reminders = Reminder.objects.filter(user=owner)

        # Логика сохранения напоминания через POST
        if request.method == 'POST':
            title = request.POST.get('title')
            date = request.POST.get('date')
            if title and date:
                Reminder.objects.create(user=owner, title=title, date=date)

    return render(request, 'profile.html', {
        'customuser': owner,
        'reminders': reminders
    })


class UpdateProfileView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        form = UpdateProfileForm(instance=request.user)
        return render(
            request,
            'profile_update.html',
            {'form': form}
        )

    def post(self, request):
        form = UpdateProfileForm(
            instance=request.user,
            data=request.POST,
            files=request.FILES
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account is successfully updated.')
            return redirect(
                'users:profile',
                request.user.username
            )

        return render(
            request,
            'profile_update.html',
            {'form': form}
        )


class AddRemoveSavedView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)

        saved = Saved.objects.filter(
            author=request.user,
            product=product
        )

        if saved.exists():
            saved.delete()
            messages.info(request, 'Removed.')
        else:
            Saved.objects.create(
                author=request.user,
                product=product
            )
            messages.info(request, 'Saved.')

        return redirect(request.META.get('HTTP_REFERER', '/'))


class SavedView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        q = request.GET.get('q', '')
        saveds = Saved.objects.filter(author=request.user)

        if q:
            products = Product.objects.filter(title__icontains=q)
            saveds = saveds.filter(product__in=products)

        return render(
            request,
            'saveds.html',
            {'saveds': saveds}
        )


class RecentlyViewedView(View):
    def get(self, request):
        r_viewed = request.session.get('recently_viewed', [])
        products = Product.objects.filter(id__in=r_viewed)

        q = request.GET.get('q', '')
        if q:
            products = products.filter(title__icontains=q)

        return render(
            request,
            'recently_viewed.html',
            {'products': products}
        )

# -------- calendar


@login_required
def profile_calendar(request):
    reminders = Reminder.objects.filter(user=request.user)


    return render(request, 'profile.html', {
        'reminders': reminders
    })

# ------------------Transaction--------------


@login_required
def deposit_money(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        if amount and float(amount) > 0:
            # Создаем запись о транзакции (она еще не подтверждена)
            Transaction.objects.create(user=request.user, amount=amount)
            messages.success(request, 'Request sent! Admin will confirm your balance soon.')
        else:
            messages.error(request, 'Invalid amount.')

    return redirect(request.META.get('HTTP_REFERER', '/'))



@login_required
def checkout_all(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('users:cart')

    total_price = 0
    items_to_buy = []

    # Сначала проверяем наличие товаров и считаем общую сумму
    for p_id, quantity in cart.items():
        product = get_object_or_404(Product, id=p_id)
        if product.count < quantity:
            messages.error(request, f"Not enough stock for {product.title}")
            return redirect('users:cart')
        total_price += product.price * quantity
        items_to_buy.append({'product': product, 'quantity': quantity})

    # Проверяем баланс
    if request.user.balance < total_price:
        messages.error(request, "Insufficient funds on your balance.")
        return redirect('users:cart')

    # Если всё ок — списываем деньги и создаем заказы
    request.user.balance -= total_price
    request.user.save()

    for item in items_to_buy:
        product = item['product']
        # Уменьшаем остаток
        product.count -= item['quantity']
        product.save()
        # Создаем запись в истории для каждой единицы или товара
        Order.objects.create(
            user=request.user,
            product=product,
            price=product.price * item['quantity'],
            quantity=item['quantity']
        )

    # Очищаем корзину
    request.session['cart'] = {}
    messages.success(request, "Success! Your order has been placed.")
    return redirect('users:orders')

@login_required
def cart_clear(request):
    request.session['cart'] = {}
    return redirect('users:cart')

# -------- by----
from products.models import Product


@login_required
def buy_now(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        # Получаем количество из скрытого поля (которое заполнил JS) или из обычного
        quantity = int(request.POST.get('quantity_hidden', 1))

        if request.user.balance >= (product.price * quantity):
            if product.count >= quantity:
                # 1. Снимаем деньги
                request.user.balance -= (product.price * quantity)
                request.user.save()

                # 2. Уменьшаем остаток товара
                product.count -= quantity
                product.save()

                # 3. ВАЖНО: Создаем запись в истории заказов
                Order.objects.create(
                    user=request.user,
                    product=product,
                    price=product.price * quantity,
                    quantity=quantity
                )

                messages.success(request, "Покупка совершена!")
                return redirect('users:orders')  # Перенаправляем на страницу истории
            else:
                messages.error(request, "Недостаточно товара на складе.")
        else:
            messages.error(request, "Недостаточно средств.")

    return redirect('products:detail', product_id=product_id)


@login_required
def add_to_cart(request, product_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})

        p_id = str(product_id)
        if p_id in cart:
            cart[p_id] += quantity
        else:
            cart[p_id] = quantity

        request.session['cart'] = cart
        messages.success(request, f"Добавлено в корзину: {quantity} шт.")

    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def orders_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-date')
    return render(request, 'orders.html', {'orders': orders})


@login_required
def cart_view(request):
    cart = request.session.get('cart', {})
    products = []
    total_price = 0

    # Получаем товары из БД по ID из сессии
    for p_id, quantity in cart.items():
        product = get_object_or_404(Product, id=p_id)
        total_price += product.price * quantity
        products.append({'product': product, 'quantity': quantity})

    return render(request, 'carts.html', {'products': products, 'total_price': total_price})

@login_required
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.delete()
    messages.success(request, "Запись удалена из истории.")
    return redirect('users:orders')

@login_required
def clear_orders(request):
    if request.method == 'POST':
        Order.objects.filter(user=request.user).delete()
        messages.success(request, "Вся история заказов очищена.")
    return redirect('users:orders')