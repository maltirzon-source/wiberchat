from django.urls import path
from chat import views
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView, RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- SPLASH SCREEN ---
    path('', TemplateView.as_view(template_name='chat/splash.html'), name='splash'),

    # --- ACCUEIL & CONTACTS ---
    path('chats/', views.chat_list, name='chat_list'),
    path('new-chat/', views.new_chat, name='new_chat'),
    path('pin-chat/<str:username>/', views.pin_chat, name='pin_chat'),

    # --- AUTHENTIFICATION ---
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='chat/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # --- CHAT PRIVÉ ---
    path('chat/<str:username>/', views.chat_room, name='chat_room'),
    path('delete-message/<int:pk>/', views.delete_message, name='delete_message'),
    path('delete-conversation/<str:username>/', views.delete_conversation, name='delete_conversation'),

    # --- API OFFLINE ---
    path('api/send-message/', views.api_send_message, name='api_send_message'),

    # --- FIL D'ACTUALITÉS & STATUTS ---
    path('actus/', views.status_list, name='status_list'),
    path('status/add/', views.add_status, name='add_status'),
    path('like/<int:pk>/', views.like_statut, name='like_statut'),
    path('vote/<int:option_id>/', views.vote_sondage, name='vote_sondage'),  # NOUVEAU
    path('delete-statut/<int:pk>/', views.delete_statut, name='delete_statut'),

    # --- PROFIL ---
    path('profile/', views.profile, name='profile'),

    # --- PWA & MODE HORS-LIGNE ---
    path('service-worker.js', TemplateView.as_view(
        template_name="service-worker.js",
        content_type='application/javascript'),
        name='service-worker.js'),
    path('manifest.json', RedirectView.as_view(url='/static/manifest.json')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)