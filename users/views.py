from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .forms import SignupForm, UpdateProfileForm
from .models import CustomUser, Saved ,Reminder
from products.models import Product


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

