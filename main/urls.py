
from django.urls import path
from .views import IndexView, category_view

app_name = 'main' #=> main:index
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('<str:category_name>/category', category_view, name='category'),
]
