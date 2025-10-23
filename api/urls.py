from django.urls import path
from .views import *

urlpatterns = [
    # Método para registrar un nuevo usuario
    path('register/', RegistroView.as_view(), name='register'),
    # Método para iniciar sesión y obtener tokens
    path('login/', LoginView.as_view(), name='login'),
    # Método para refrescar el token de acceso
    path('refresh/', RefreshTokenView.as_view(), name='refresh'),
    
    # Método para obtener información del Usuario
    path('get-user-info/<str:pk>/', UserInfoView.as_view(), name='get-user-info'),
    # Método para promover learner a mentor
    path('learner-to-mentor/', LearnerToMentorView.as_view(), name='learner-to-mentor'),
    
    # Método para añadir información de un learner
    path('post-learner/', LearnerUpdateInfoView.as_view(), name='post-learner'),
    # Método para añadir información de un mentor
    path('post-mentor/', MentorUpdateInfoView.as_view(), name='post-mentor'),
    
    # Método para que el mentor cree una nueva sesión
    path('create-session/', CreateSessionView.as_view(), name='create-session')
]