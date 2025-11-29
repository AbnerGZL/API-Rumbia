import uuid
import jwt
from datetime import datetime, timezone
from django.conf import settings
from .models import *
from .serializer import *
from django.utils import timezone
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
# from .jwt_utils import decode_token, refresh_token_is_valid, revoke_refresh_token, generate_access_token, generate_refresh_token
from django.contrib.auth.hashers import check_password, make_password

from rest_framework.parsers import MultiPartParser, FormParser
import os

from django.db.models import Q

ALGO = settings.JWT_ALGORITHM
SECRET = settings.SECRET_KEY

def generate_access_token(user):
    now = datetime.now()
    exp = now + settings.JWT_ACCESS_TOKEN_LIFETIME
    payload = {
        'type': 'access',
        'exp': exp,
        'iat': now,
        'sub': str(user.id_user),   # identificador que tú usas
        # 'email': user.email
    }
    token = jwt.encode(payload, SECRET, algorithm=ALGO)
    return token

def generate_refresh_token(user):
    now = datetime.now()
    exp = now + settings.JWT_REFRESH_TOKEN_LIFETIME
    jti = str(uuid.uuid4())
    payload = {
        'type': 'refresh',
        'exp': exp,
        'iat': now,
        'sub': str(user.id_user),
        'jti': jti
    }
    token = jwt.encode(payload, SECRET, algorithm=ALGO)

    # Guardar el refresh token en BD para poder revocar/rotar
    RefreshTokenModel.objects.create(
        user=user,
        jti=jti,
        expires_at=timezone.make_aware(datetime.fromtimestamp(exp.timestamp()))
    )
    return token

def decode_token(token, verify_exp=True):
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGO], options={'verify_exp': verify_exp})
        return payload
    except jwt.ExpiredSignatureError:
        raise
    except jwt.InvalidTokenError:
        raise
    
def revoke_refresh_token(jti):
    try:
        rt = RefreshTokenModel.objects.get(jti=jti)
        rt.revoked = True
        rt.save()
    except RefreshTokenModel.DoesNotExist:
        pass

def refresh_token_is_valid(jti):
    try:
        rt = RefreshTokenModel.objects.get(jti=jti, revoked=False)
        return not rt.is_expired()
    except RefreshTokenModel.DoesNotExist:
        return False

class RegistroView(APIView):
    def post(self, request):
        nuevoUser = request.data.copy()
        nuevoUser['password_hash'] = make_password(nuevoUser['password'])
        nuevoUser['user_code'] = str(uuid.uuid4()).replace('-','')[:10]
        tipo = nuevoUser['tipo']  # 'learner' o 'mentor'
        
        match tipo:
            case 'learner':
                pass

            case 'mentor':
                if not request.data.get("language") or not request.data.get("description"):
                    return Response({"error": "Campos obligatorios no enviados (language, description)."}, status=400)

                if not request.data.get("career") and not request.data.get("alt_career"):
                    return Response({"error": "Campos obligatorios no enviados (career_id, alt_career)."}, status=400)

            case _:
                return Response({"error": "Tipo de usuario inválido."}, status=400)           
        
        serializer = UserCreateSerializer(data=nuevoUser)
        if serializer.is_valid():
            user = serializer.save()
            
            if tipo == 'learner':
                Learner.objects.create(user=user, is_learner=1)
            elif tipo == 'mentor':
                if request.data.get("career"):
                    career = Career.objects.filter(id_career=request.data.get("career")).first()
                else:
                    career = None
                Mentor.objects.create(
                    user=user,
                    career=career,
                    is_mentor=1,
                    alt_career=request.data.get("alt_career"),
                    language=request.data.get("language"),
                    description=request.data.get("description")
                    )
            
            access = generate_access_token(user)
            refresh = generate_refresh_token(user)
            response = Response({"user_code": user.user_code}, status=status.HTTP_201_CREATED)

            response.set_cookie(
                key='access_token',
                value=access,
                httponly=True,
                secure=True,
                max_age=int(settings.JWT_ACCESS_TOKEN_LIFETIME.total_seconds()),
                samesite='Lax',
                path='/'
            )
            response.set_cookie(
                key='refresh_token',
                value=refresh,
                httponly=True,
                secure=True,
                max_age=int(settings.JWT_REFRESH_TOKEN_LIFETIME.total_seconds()),
                samesite='Lax',
                path='/',
                # path='/api/refresh/'
            )

            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            return Response({'detail': 'Email y password requeridos'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'Credenciales inválidas'}, status=status.HTTP_401_UNAUTHORIZED)

        if not check_password(password, user.password_hash):
            return Response({'detail': 'Credenciales inválidas'}, status=status.HTTP_401_UNAUTHORIZED)

        access = generate_access_token(user)
        refresh = generate_refresh_token(user)

        response = Response({'user_code': user.user_code}, status=status.HTTP_200_OK)

        # Set cookies (usa secure=True en producción con HTTPS)
        response.set_cookie(
            key='access_token',
            value=access,
            httponly=True,
            secure=True,
            max_age=int(settings.JWT_ACCESS_TOKEN_LIFETIME.total_seconds()),
            samesite='Lax',
            path='/'
        )
        response.set_cookie(
            key='refresh_token',
            value=refresh,
            httponly=True,
            secure=True,
            max_age=int(settings.JWT_REFRESH_TOKEN_LIFETIME.total_seconds()),
            samesite='Lax',
            path='/',
            # path='/api/refresh/'
        )

        return response    
        
class RefreshTokenView(APIView):
    def post(self, request):
            # Preferimos leer cookie; si no, leer body
            refresh_token = request.COOKIES.get('refresh_token')
            if not refresh_token:
                return Response({'detail': 'Refresh token not found'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                payload = decode_token(refresh_token)  # verifica exp por defecto
            except jwt.ExpiredSignatureError:
                return Response({'detail': 'Refresh token expired'}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({'detail': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)

            if payload.get('type') != 'refresh':
                return Response({'detail': 'Token no es refresh'}, status=status.HTTP_400_BAD_REQUEST)

            jti = payload.get('jti')
            user_id = payload.get('sub')

            if not refresh_token_is_valid(jti):
                return Response({'detail': 'Refresh token revoked or invalid'}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                user = User.objects.get(id_user=int(user_id))
            except User.DoesNotExist:
                return Response({'detail': 'Usuario no existe'}, status=status.HTTP_401_UNAUTHORIZED)

            # Rotación: invalidar el refresh actual y crear uno nuevo
            revoke_refresh_token(jti)
            new_refresh = generate_refresh_token(user)
            new_access = generate_access_token(user)

            response = Response({'message': 'Tokens refreshed'}, status=status.HTTP_200_OK)
            response.set_cookie(
                key='access_token',
                value=new_access,
                httponly=True,
                secure=True,
                max_age=int(settings.JWT_ACCESS_TOKEN_LIFETIME.total_seconds()),
                samesite='Lax',
                path='/'
            )
            response.set_cookie(
                key='refresh_token',
                value=new_refresh,
                httponly=True,
                secure=True,
                max_age=int(settings.JWT_REFRESH_TOKEN_LIFETIME.total_seconds()),
                samesite='Lax',
                path='/api/refresh/'
            )
            return response

class UpdateUserView(APIView):
    def post(self, request):
        user = get_object_or_404(User, user_code=request.data.get("user_code"))
        
        update = request.data.copy()
        if request.data.get("password"):
            update['password_hash'] = make_password(request.data.get("password"))
                
        serializer = UserCreateSerializer(user, data=update, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetUserInfoView(APIView):
    def get(self, request, pk):
        user = get_object_or_404(User, user_code=pk)
        data = UserSerializer(user).data
        if hasattr(user, 'mentor'):
            if user.mentor.is_mentor:
                mentor = get_object_or_404(Mentor, id_mentor=user.mentor.id_mentor)
                print("este es el id: ",mentor.id_mentor)
                if hasattr(mentor, 'professionalprofile'):
                    profile = mentor.professionalprofile
                    data['professional_profile'] = Professional_ProfileSerializer(profile).data
                elif hasattr(mentor, 'studentprofile'):
                    profile = mentor.studentprofile
                    data['student_profile'] = Student_ProfileSerializer(profile).data
                return Response(data, status=status.HTTP_200_OK)
        return Response(data, status=status.HTTP_200_OK) 

class LearnerUpdateInfoView(APIView):
    def post(self, request):
        if request.data.get("user_code") is None:
            return Response({'error': 'Se requiere el user_code para actualizar el perfil de usuario'}, status=400)
        
        learner = get_object_or_404(User, user_code=request.data.get("user_code")).learner
        if learner is None:
            return Response({'error': 'Este usuario no tiene un perfil de aprendiz asociado'}, status=404)
        
        serializer = LearnerSerializer(learner, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MentorUpdateInfoView(APIView):
    def post(self, request):
        user = get_object_or_404(User, user_code=request.data.get("user_code"))
        mentor = user.mentor
        if not hasattr(user, 'mentor'):
            return Response({'error': 'Este usuario no es un mentor'}, status=400)
        
        if request.data.get("tipo_mentor") == "professional":                
            if hasattr(mentor, 'professionalprofile'):
                profile = mentor.professionalprofile
                serializer = Professional_ProfileSerializer(profile, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            else:
                nuevoMentor = request.data.copy()
                nuevoMentor['mentor'] = mentor.id_mentor
                serializer = Professional_ProfileSerializer(data=nuevoMentor)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)            
        
        if request.data.get("tipo_mentor") == "student":
            if hasattr(mentor, 'studentprofile'):
                profile = mentor.studentprofile
                serializer = Student_ProfileSerializer(profile, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            else:
                nuevoMentor = request.data.copy()
                nuevoMentor['mentor'] = mentor.id_mentor
                serializer = Student_ProfileSerializer(data=nuevoMentor)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LearnerToMentorView(APIView):
    def post(self, request):
        user = get_object_or_404(User, user_code=request.data.get("user_code"))
        
        if hasattr(user, 'mentor'):
            return Response({'error': 'Este usuario ya es un mentor'}, status=400)

        career = None
        if request.data.get("career"):
            career = Career.objects.filter(id_career=request.data.get("career")).first()

        mentor_data = {
            'user': user.id_user,
            'career': career.id_career if career else None,
            'is_mentor': True,
            'alt_career': request.data.get("alt_career"),
            'language': request.data.get("language"),
            'description': request.data.get("description"),
        }

        serializer = MentorSerializer(data=mentor_data)
        if serializer.is_valid():
            serializer.save()
            learner = getattr(user, 'learner', None)
            if learner:
                learner.is_learner = False
                learner.save()

            return Response({'message': 'El usuario ha sido promovido a mentor'}, status=201)
        
        return Response(serializer.errors, status=400)
    
class CreateSessionView(APIView):
    def post(self, request):
        user = get_object_or_404(User, user_code=request.data.get("user_code"))
        
        if not hasattr(user, 'mentor'):
            return Response({'error': 'Este usuario no es un mentor'}, status=400)
        
        mentor = user.mentor
        fecha = datetime.now().strftime("%Y%m%d")
        session_data = request.data.copy()
        
        session_data['mentor'] = mentor.id_mentor
        session_data['uuid'] =  f"{fecha}{str(uuid.uuid4().hex)}"
        session_data['session_status'] = "scheduled"
        serializer = SessionCreateSerializer(data=session_data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        
        return Response(serializer.errors, status=400)

class GetSessionsActivesView(APIView):
    def get(self, request):
        # /api/sessions/?session_status=active&start_date=2025-11-05&end_date=2025-11-10&career_id=2&category_id=1
        session_status = request.query_params.get('session_status', None) # Fijo
        career_id = request.query_params.get('career_id', None)
        category_id = request.query_params.get('category_id', None)
        
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        
        user_code = request.query_params.get('mentor', None)
        user = None
        if user_code is not None:
            user = User.objects.filter(user_code=user_code).first()
        
        mentor = user.mentor if user else None

        sessions = Session.objects.select_related(
            'mentor', 'mentor__career', 'mentor__career__category'
        ).all()

        # --- Filtros dinámicos ---
        filters = Q()
                    
        if start_date and end_date:
            # Entre ambas fechas (rango cerrado)
            filters &= Q(schedule_date__date__range=[start_date, end_date])
        elif start_date:
            # Desde start_date hacia adelante
            filters &= Q(schedule_date__date__gte=start_date)
        elif end_date:
            # Hasta end_date hacia atrás
            filters &= Q(schedule_date__date__lte=end_date)
            
        if session_status:
            filters &= Q(session_status=session_status)

        if career_id:
            filters &= Q(mentor__career__id_career=career_id)

        if category_id:
            filters &= Q(mentor__career__category__id_category=category_id)
        
        if mentor:
            filters &= Q(mentor=mentor)

        sessions = sessions.filter(filters).order_by('-schedule_date')
        serializer = SessionSerializer(sessions, many=True)
        
        return Response(
            {
                "count": len(serializer.data),
                "filters_applied": {
                    "mentor": mentor.id_mentor if mentor else None,
                    "status": session_status,
                    "career_id": career_id,
                    "category_id": category_id,
                    "start_date": start_date,
                    "end_date": end_date
                },
                "results": serializer.data
            },
            status=status.HTTP_200_OK)

        # serializer = SessionSerializer(sessions, many=True)
        # return Response(serializer.data, status=status.HTTP_200_OK)

class GetCareersView(APIView):
    def get(self, request):
        careers = Career.objects.select_related('category').all()
        serializer = CareerSerializer(careers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetCategoriesView(APIView):
    def get(self, request):
        categories = CareerCategories.objects.all()
        serializer = CategoriesSerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
class UploadMentorImageView(APIView):
    parser_classes = [MultiPartParser, FormParser]  # <- importante para manejar archivos

    def post(self, request):
        user_code = request.data.get("user_code")
        image_file = request.FILES.get("profile_img")

        if not user_code or not image_file:
            return Response({"error": "user_code e image son requeridos"}, status=400)
        
        if image_file.size > 15 * 1024 * 1024:  # 15MB
            return Response({"error": "El tamaño del archivo excede el límite de 5MB"}, status=400)
        
        if image_file.content_type not in ['image/jpeg', 'image/png', 'image/jpg']:
            return Response({"error": "Tipo de archivo no soportado. Solo se permiten JPEG, PNG o JPG."}, status=400)

        user = get_object_or_404(User, user_code=user_code)
        mentor = user.mentor

        # Construir la ruta personalizada
        folder_path = os.path.join(settings.MEDIA_ROOT, f"mentors/{user_code}/")
        os.makedirs(folder_path, exist_ok=True)

        image_file.name = f"profile_img{user_code}{os.path.splitext(image_file.name)[1]}"
        
        if mentor.profile_img:
            # Eliminar la imagen anterior si existe
            old_image_path = os.path.join(settings.MEDIA_ROOT, image_file.name)
            if os.path.exists(old_image_path):
                os.remove(old_image_path)
        
        # Guardar con el nombre del usuario
        file_path = os.path.join(folder_path, image_file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in image_file.chunks():
                destination.write(chunk)

        # Guardar la referencia en la base de datos
        relative_path = f"mentors/{user_code}/{image_file.name}"
        mentor.profile_img = relative_path
        mentor.save()

        return Response({"message": "Imagen subida correctamente", "path": relative_path}, status=200)

class UpdateSessionView(APIView):
    def post(self, request):
        session = get_object_or_404(Session, uuid=request.data.get("uuid"))
        serializer = SessionCreateSerializer(session, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class InscribeLearnerView(APIView):
    def post(self, request):
        user = get_object_or_404(User, user_code=request.data.get("user_code"))
        # learner = user.learner
        # if not hasattr(user, 'learner'):
        #     return Response({'error': 'Este usuario no es un aprendiz'}, status=400)
        
        session = get_object_or_404(Session, uuid=request.data.get("uuid"))
        
        if DataSession.objects.filter(user=user, session=session).exists():
            return Response({'error': 'El aprendiz ya está inscrito en esta sesión'}, status=400)
        
        inscription = DataSession.objects.create(
            session=session,
            user=user
        )
        
        serializer = Data_SessionSerializer(inscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class GetSessionInfoView(APIView):
    def get(self, request, pk):
        session = get_object_or_404(Session, uuid=pk)
        serializer = SessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetSessionsByUserView(APIView):
    def get(self, request, pk):
        user = get_object_or_404(User, user_code=pk)
        mentor = user.mentor if hasattr(user, 'mentor') else None
        
        # learner solo tiene sesiones de aprendizaje mientras que mentor tiene sesiones de mentoría
        tipo_session = request.query_params.get('tipo_session', None)  # 'learner' o 'mentor' FIJO
        
        session_status = request.query_params.get('session_status', None) # Fijo
        
        if tipo_session not in ['learner', 'mentor']:
            return Response({'error': 'tipo_session inválido. Debe ser "learner" o "mentor".'}, status=400)
        
        filters = Q()
        sessions = None
        
        if tipo_session == 'learner':
            filters &= Q(user=user)

            if session_status:
                filters &= Q(session__session_status=session_status)

            sessions = DataSession.objects.select_related('session').filter(filters).order_by('-session__schedule_date')
            
        if tipo_session == 'mentor':
            filters &= Q(mentor=mentor)

            if session_status:
                filters &= Q(session_status=session_status)
            sessions = Session.objects.select_related('mentor').filter(filters).order_by('-schedule_date')

        serializer = SessionSerializer(sessions, many=True)
        
        return Response(
            {
                "count": len(serializer.data),
                "filters_applied": {
                    "user": user.user_code,
                    "tipo_session": tipo_session,
                    "session_status": session_status,
                },
                "results": serializer.data
            },
            status=status.HTTP_200_OK)