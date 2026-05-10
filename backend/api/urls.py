from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.register),
    path('auth/login/', views.login),
    path('auth/logout/', views.logout),

    # User / Profile
    path('me/', views.me),
    path('me/update/', views.update_profile),
    path('users/search/', views.search_users),
    path('users/<str:username>/', views.user_profile),
    path('users/<str:username>/posts/', views.user_posts),
    path('users/<str:username>/follow/', views.follow_user),

    # Posts
    path('feed/', views.feed),
    path('home/', views.home_feed),
    path('posts/', views.create_post),
    path('posts/<int:pk>/', views.post_detail),
    path('posts/<int:pk>/like/', views.like_post),

    # Comments
    path('posts/<int:pk>/comments/', views.post_comments),
    path('comments/<int:pk>/', views.delete_comment),
]
