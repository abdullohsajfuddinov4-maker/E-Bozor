from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse

from .forms import NewProductForm, ProductForm
from .models import Product, ProductImage, Comment


@login_required(login_url='login')
def new_product(request):
    if request.method == 'GET':
        form = NewProductForm(user=request.user)
        return render(request, 'product_new.html', {'form': form})

    if request.method == 'POST':
        form = NewProductForm(
            request.POST,
            user=request.user
        )

        if form.is_valid():
            product = form.save()

            # загрузка нескольких изображений
            images = request.FILES.getlist('images')
            for image in images:
                ProductImage.objects.create(
                    product=product,
                    image=image
                )

            messages.success(request, 'Product successfully created!')
            return redirect('main:index')

        return render(request, 'product_new.html', {'form': form})


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # recently viewed
    recently_viewed = request.session.get('recently_viewed', [])
    if product.id not in recently_viewed:
        recently_viewed.append(product.id)
        request.session['recently_viewed'] = recently_viewed

    return render(request, 'product_detail.html', {
        'product': product
    })

@login_required(login_url='login')
def product_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user != product.author:
        messages.error(request, 'Access denied!')
        return redirect('main:index')

    if request.method == 'GET':
        form = ProductForm(instance=product)
        return render(
            request,
            'product_update.html',
            {'form': form, 'product': product}
        )

    if request.method == 'POST':
        form = ProductForm(
            instance=product,
            data=request.POST
        )

        if form.is_valid():
            form.save()

            # если загрузили новые изображения — заменяем старые
            images = request.FILES.getlist('images')
            if images:
                ProductImage.objects.filter(product=product).delete()
                for image in images:
                    ProductImage.objects.create(
                        product=product,
                        image=image
                    )

            messages.success(request, 'Product successfully updated!')
            return redirect('products:detail', product.id)

        return render(
            request,
            'product_update.html',
            {'form': form, 'product': product}
        )


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
        Comment.objects.create(
            author=request.user,
            product=product,
            body=request.POST.get('body'),
            rating=request.POST.get('rating')  # ВАЖНО
        )
        return redirect('products:detail', product_id)



@login_required(login_url='login')
def delete_comment(request, product_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user == comment.author:
        comment.delete()
        messages.success(request, 'Comment deleted')

    return redirect('products:detail', product_id)
