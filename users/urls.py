
from .views import (SignupView,
                    profile_view,
                    UpdateProfileView,
                    AddRemoveSavedView,
                    SavedView,
                    RecentlyViewedView,
                    profile_calendar,
                    logout_view,
                    )
from django.urls import path

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


]
