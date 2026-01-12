from django.shortcuts import render
from django.views import View
from products.models import Product, Category
from django.shortcuts import get_object_or_404


# Create your views here.

def for_all_pages(request):
    categories = Category.objects.all()
    return {"categories": categories}


class IndexView(View):
    def get(self, request):
        products = Product.objects.all()
        q = request.GET.get('q', '')
        if q:
            products = products.filter(title__icontains=q)
        return render(request, "index.html", {'products': products})


def category_view(request, category_name):
    # Базовый набор товаров
    products = Product.objects.filter(category__name=category_name)

    # 1. Поиск
    query = request.GET.get('q')
    if query:
        products = products.filter(title__icontains=query)

    # 2. Мин цена
    min_price = request.GET.get('min_price')
    if min_price and min_price.isdigit():  # Добавили проверку на число
        products = products.filter(price__gte=min_price)

    # 3. Макс цена
    max_price = request.GET.get('max_price')
    if max_price and max_price.isdigit():
        products = products.filter(price__lte=max_price)

    # 4. Сортировка (ИСПРАВЛЕНО: используем 'date' вместо 'created_at')
    sort = request.GET.get('sort', '-date')

    # Проверка, чтобы Django не упал, если в sort придет несуществующее поле
    allowed_sorts = ['price', '-price', 'date', '-date']
    if sort not in allowed_sorts:
        sort = '-date'

    products = products.order_by(sort)

    context = {
        'category': category_name,
        'products': products,
    }
    return render(request, 'category.html', context)



