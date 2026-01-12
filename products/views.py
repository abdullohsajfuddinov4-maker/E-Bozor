from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse

from .forms import NewProductForm, ProductForm
from .models import Product, ProductImage, Comment


@login_required(login_url='login')
def new_product(request):
    if request.method == 'POST':
        form = NewProductForm(request.POST, request.FILES, user=request.user)
        img1 = request.FILES.get('image1')
        img2 = request.FILES.get('image2')
        img3 = request.FILES.get('image3')

        if not (img1 and img2 and img3):
            messages.error(request, 'Пожалуйста, загрузите все 3 фотографии.')
            return render(request, 'product_new.html', {'form': form})

        if form.is_valid():
            product = form.save()
            for img in [img1, img2, img3]:
                ProductImage.objects.create(product=product, image=img)
            messages.success(request, 'Продукт создан!')
            return redirect('main:index')
    else:
        form = NewProductForm(user=request.user)
    return render(request, 'product_new.html', {'form': form})


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Проверяем, авторизован ли пользователь и оставлял ли он уже комментарий
    already_rated = False
    if request.user.is_authenticated:
        already_rated = product.comments.filter(author=request.user).exists()

    # recently viewed (твой существующий код)
    recently_viewed = request.session.get('recently_viewed', [])
    if product.id not in recently_viewed:
        recently_viewed.append(product.id)
        request.session['recently_viewed'] = recently_viewed

    return render(request, 'product_detail.html', {
        'product': product,
        'already_rated': already_rated  # Передаем переменную в шаблон
    })



@login_required(login_url='login')
def add_product_image(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user == product.author and request.method == 'POST':
        images = request.FILES.getlist('images')
        for img in images:
            ProductImage.objects.create(product=product, image=img)
        messages.success(request, 'Фото добавлено!')
    return redirect('products:detail', product_id=product.id)


@login_required(login_url='login')
def product_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user != product.author:
        messages.error(request, 'Access denied!')
        return redirect('main:index')

    if request.method == 'POST':
        form = ProductForm(data=request.POST, instance=product)

        # Получаем новые файлы из трех полей
        img1 = request.FILES.get('image1')
        img2 = request.FILES.get('image2')
        img3 = request.FILES.get('image3')

        if form.is_valid():
            form.save()

            # Если пользователь загрузил все 3 новых изображения
            if img1 and img2 and img3:
                # Удаляем старые фото из базы
                product.images.all().delete()

                # Создаем новые записи
                for img in [img1, img2, img3]:
                    ProductImage.objects.create(product=product, image=img)
                messages.success(request, 'Product and all images updated!')
            else:
                messages.success(request, 'Product details updated (images remained the same).')

            return redirect('products:detail', product.id)
    else:
        form = ProductForm(instance=product)

    return render(request, 'product_update.html', {
        'form': form,
        'product': product
    })



@login_required(login_url='login')
def product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user != product.author:
        messages.error(request, 'Access denied!')
        return redirect('main:index')

    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted!')
        return redirect('main:index')

    return render(
        request,
        'product_delete.html',
        {'product': product}
    )


@login_required(login_url='login')
def new_comment(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        body = request.POST.get('body')
        # Получаем рейтинг, если его нет в POST — ставим 0
        rating = request.POST.get('rating', 0)

        # Если пришла пустая строка из формы, тоже превращаем в 0
        if not rating:
            rating = 0

        # Проверяем, был ли уже отзыв с рейтингом > 0
        already_rated = Comment.objects.filter(product=product, author=request.user, rating__gt=0).exists()

        if already_rated:
            # Если уже оценивал — сохраняем только текст, принудительно ставим рейтинг 0
            Comment.objects.create(
                author=request.user,
                product=product,
                body=body,
                rating=0
            )
            messages.info(request, 'Ваш дополнительный комментарий добавлен.')
        else:
            # Если это первый раз и рейтинга нет — это ошибка
            if int(rating) == 0:
                messages.error(request, 'Пожалуйста, выберите оценку при первом отзыве.')
                return redirect('products:detail', product_id=product.id)

            Comment.objects.create(
                author=request.user,
                product=product,
                body=body,
                rating=rating
            )
            messages.success(request, 'Ваш отзыв принят!')

        return redirect('products:detail', product_id=product.id)



@login_required(login_url='login')
def delete_comment(request, product_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user == comment.author:
        comment.delete()
        messages.success(request, 'Comment deleted')

    return redirect('products:detail', product_id)
