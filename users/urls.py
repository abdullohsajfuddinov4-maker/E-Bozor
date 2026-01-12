
from .views import (SignupView,
                    profile_view,
                    UpdateProfileView,
                    AddRemoveSavedView,
                    SavedView,
                    RecentlyViewedView,
                    profile_calendar,
                    logout_view,
                    deposit_money,
                    buy_now,
                    add_to_cart, orders_history, cart_view, checkout_all, cart_clear, delete_order, clear_orders,

                    )
from django.urls import path
from . import views

app_name='users'
urlpatterns = [
    path('signup', SignupView.as_view(), name='signup'),
    path('profile/<str:username>/',profile_view, name='profile'),
    path('update', UpdateProfileView.as_view(), name='update'),
    path('addremovesaved/<int:product_id>', AddRemoveSavedView.as_view(), name='addremovesaved'),
    path('saveds', SavedView.as_view(), name='saveds'),
    path('recently-viewed', RecentlyViewedView.as_view(), name='recently_viewed'),
    path('calendar/', profile_calendar, name='calendar'),
    path('logout/', logout_view, name='logout'),
    path('deposit/', deposit_money, name='deposit'),
    path('buy-now/<int:product_id>/', buy_now, name='buy_now'),
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('orders/', orders_history, name='orders'),
    path('cart/', cart_view, name='cart'),
    path('cart/checkout/', checkout_all, name='checkout_all'),
    path('cart/clear/',cart_clear, name='cart_clear'),
    path('orders/delete/<int:order_id>/', delete_order, name='delete_order'),
    path('orders/clear/', clear_orders, name='clear_orders'),
    path('chats/', views.chat_list, name='chat_list'),
    path('chats/<int:user_id>/', views.chat_detail, name='chat_detail'),
    path('chats/<int:user_id>/block/', views.block_user, name='block_user'),
    path('chats/<int:user_id>/unblock/', views.unblock_user, name='unblock_user'),

]
