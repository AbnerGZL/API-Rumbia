from django.urls import path
from django.conf.urls.static import static
from .views import *

urlpatterns = [
    # Método para registrar un nuevo usuario
    path('register/', RegistroView.as_view(), name='register'),
    # Método para iniciar sesión y obtener tokens
    path('login/', LoginView.as_view(), name='login'),
    # Método para refrescar el token de acceso
    path('refresh/', RefreshTokenView.as_view(), name='refresh'),
    
    # Método para obtener información del Usuario
    path('get-user-info/<str:pk>/', GetUserInfoView.as_view(), name='get-user-info'),
    # Método para promover learner a mentor
    path('learner-to-mentor/', LearnerToMentorView.as_view(), name='learner-to-mentor'),
    
    # Método para añadir información de un learner
    path('post-learner/', LearnerUpdateInfoView.as_view(), name='post-learner'),
    # Método para añadir información de un mentor
    path('post-mentor/', MentorUpdateInfoView.as_view(), name='post-mentor'),
    
    # Método para que el mentor cree una nueva sesión
    path('create-session/', CreateSessionView.as_view(), name='create-session'),
    # Método para listar sesiones activas con filtros dinamicos
    path('get-sessions/', GetSessionsActivesView.as_view(), name='sessions'),
    # Método para listar carreras disponibles
    path('get-careers/', GetCareersView.as_view(), name='get-careers'),
    # Método para listar catgorias de carreas
    path('get-categories/', GetCategoriesView.as_view(), name='get-categories'),
    
    # Método para cargar imagen de perfil de mentor
    path('post-mentor-image/', UploadMentorImageView.as_view(), name='mentor-image'),
    # Método para actualizar informacion de una sesion
    path('update-session/', UpdateSessionView.as_view(), name='update-session'),
    
    # Método para actualizar informacion de una sesion
    path('inscribe-learner/', InscribeLearnerView.as_view(), name='inscribe-learner'),
    # Método para obtener informacion de una sesion
    path('get-session-info/<str:pk>/', GetSessionInfoView.as_view(), name='get-session-info'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)