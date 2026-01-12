from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .forms import SignupForm, UpdateProfileForm
from .models import CustomUser, Saved, Reminder, Transaction, Order, BlockedUser
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

    base_total_price = 0
    items_to_buy = []

    # 1. Считаем базовую стоимость всех товаров
    for p_id, quantity in cart.items():
        product = get_object_or_404(Product, id=p_id)
        if product.count < quantity:
            messages.error(request, f"Not enough stock for {product.title}")
            return redirect('users:cart')

        base_total_price += product.price * quantity
        items_to_buy.append({'product': product, 'quantity': quantity, 'base_price': product.price})

    # --- ЛОГИКА ПРОМОКОДА ---
    discount_percent = request.session.get('discount', 0)
    discount_amount = (base_total_price * discount_percent) / 100
    final_total_price = base_total_price - discount_amount
    # ------------------------

    # 2. Проверяем баланс по финальной цене
    if request.user.balance < final_total_price:
        messages.error(request, f"Insufficient funds. Required: ${final_total_price}")
        return redirect('users:cart')

    # 3. Списываем итоговую сумму со скидкой
    request.user.balance -= final_total_price
    request.user.save()

    # 4. Обработка каждого товара
    for item in items_to_buy:
        product = item['product']
        quantity = item['quantity']

        # Уменьшаем остаток
        product.count -= quantity
        product.save()

        # Рассчитываем цену для истории заказов пропорционально скидке
        item_base_price = product.price * quantity
        item_final_price = item_base_price - (item_base_price * discount_percent / 100)

        Order.objects.create(
            user=request.user,
            product=product,
            price=item_final_price,
            quantity=quantity
        )

    # 5. Очищаем корзину и промокод
    request.session['cart'] = {}
    if 'discount' in request.session:
        del request.session['discount']
        del request.session['promo_code']

    messages.success(request, f"Success! Order placed. Total paid: ${final_total_price} (Saved ${discount_amount})")
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
        quantity = int(request.POST.get('quantity_hidden', 1))

        # --- ЛОГИКА ПРОМОКОДА ---
        discount_percent = request.session.get('discount', 0)
        base_price = product.price * quantity

        # Считаем сумму скидки и итоговую цену
        discount_amount = (base_price * discount_percent) / 100
        final_price = base_price - discount_amount
        # ------------------------

        if request.user.balance >= final_price:
            if product.count >= quantity:
                # 1. Снимаем деньги (со скидкой)
                request.user.balance -= final_price
                request.user.save()

                # 2. Уменьшаем остаток товара
                product.count -= quantity
                product.save()

                # 3. Создаем запись в истории заказов
                # В поле price лучше записывать итоговую цену, которую реально заплатил юзер
                Order.objects.create(
                    user=request.user,
                    product=product,
                    price=final_price,
                    quantity=quantity
                )

                # Удаляем скидку из сессии после покупки (опционально)
                if 'discount' in request.session:
                    del request.session['discount']
                    del request.session['promo_code']

                messages.success(request, f"Покупка совершена! Списано: ${final_price} (Скидка {discount_percent}%)")
                return redirect('users:orders')
            else:
                messages.error(request, "Недостаточно товара на складе.")
        else:
            messages.error(request, "Недостаточно средств. Нужно: $" + str(final_price))

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




# -----------message------------

from django.db.models import Q
from .models import CustomUser, Message


@login_required
def chat_detail(request, user_id):
    other_user = get_object_or_404(CustomUser, id=user_id)

    # 1. Проверка блокировки
    i_blocked_him = BlockedUser.objects.filter(blocker=request.user, blocked=other_user).exists()
    he_blocked_me = BlockedUser.objects.filter(blocker=other_user, blocked=request.user).exists()

    if request.method == "POST":
        if not i_blocked_him and not he_blocked_me:
            text = request.POST.get('text', '').strip()
            if text:
                Message.objects.create(sender=request.user, recipient=other_user, text=text)
                return redirect('users:chat_detail', user_id=user_id)

    # 2. ПОЛУЧЕНИЕ СООБЩЕНИЙ (Здесь важно имя переменной)
    chat_data = Message.objects.filter(
        (Q(sender=request.user) & Q(recipient=other_user)) |
        (Q(sender=other_user) & Q(recipient=request.user))
    ).order_by('created_at')

    # 3. ПОМЕЧАЕМ ПРОЧИТАННЫМИ (Используем то же имя chat_data)
    chat_data.filter(recipient=request.user, is_read=False).update(is_read=True)

    return render(request, 'chat.html', {
        'other_user': other_user,
        'chat_messages': chat_data,  # Передаем в шаблон
        'i_blocked_him': i_blocked_him,
        'he_blocked_me': he_blocked_me
    })
from django.db.models import Max

@login_required
def chat_list(request):

    chat_users = CustomUser.objects.filter(
        Q(sent_messages__recipient=request.user) |
        Q(received_messages__sender=request.user)
    ).annotate(
        last_msg_date=Max('sent_messages__created_at')
    ).exclude(id=request.user.id).distinct().order_by('-last_msg_date')

    blocked_ids = request.user.blocking.values_list('blocked_id', flat=True)

    return render(request, 'chat_list.html', {
        'users': chat_users,
        'blocked_ids': blocked_ids
    })


@login_required
def block_user(request, user_id):
    target_user = get_object_or_404(CustomUser, id=user_id)
    BlockedUser.objects.get_or_create(blocker=request.user, blocked=target_user)
    return redirect('users:chat_detail', user_id=user_id)

@login_required
def unblock_user(request, user_id):
    target_user = get_object_or_404(CustomUser, id=user_id)
    BlockedUser.objects.filter(blocker=request.user, blocked=target_user).delete()
    return redirect('users:chat_detail', user_id=user_id)


# ----- promokod -----
from .models import PromoCode


def apply_promo(request):
    if request.method == "POST":
        code = request.POST.get('promo_code')
        try:
            promo = PromoCode.objects.get(code__iexact=code, is_active=True)
            # Сохраняем скидку в сессии
            request.session['discount'] = promo.discount_percentage
            request.session['promo_code'] = promo.code
            messages.success(request, f"Промокод '{code}' применен! Скидка {promo.discount_percentage}%")
        except PromoCode.DoesNotExist:
            request.session['discount'] = 0
            request.session['promo_code'] = None
            messages.error(request, "Неверный или неактивный промокод")

    return redirect('users:cart')
