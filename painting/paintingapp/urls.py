from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('charity/', views.charity, name='charity'),
    path('customize/', views.customize, name='customize'),
    path('save-customized-painting/', views.save_customized_painting, name='save_customized_painting'),
    path('customized-painting/<int:pk>/', views.customized_painting_detail, name='customized_painting_detail'),
    path('search/', views.search, name='search'),
    
    # Authentication URLs
    path('signup/', views.signup, name='signup'),
    
    path('login/', auth_views.LoginView.as_view(template_name='paintingapp/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    
    # Category URLs
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    
    # Product URLs
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    
    # Cart URLs
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    
    # Order URLs
    path('order-history/', views.order_history, name='order_history'),
    
    # Artist URLs
    path('artists/', views.ArtistListView.as_view(), name='artist_list'),
    path('artist/<int:pk>/', views.ArtistDetailView.as_view(), name='artist_detail'),
    path('artist/create/', views.ArtistCreateView.as_view(), name='artist_create'),
    path('artist/<int:pk>/update/', views.ArtistUpdateView.as_view(), name='artist_update'),
    path('artist/<int:artist_id>/add-painting/', views.add_painting, name='add_painting'),
    
    # Chatbot URL
    path('chatbot/', views.chatbot, name='chatbot'),
    path('submit-drawing/', views.submit_drawing, name='submit_drawing'),
    path('submissions/', views.user_submissions, name='user_submissions'),
] 