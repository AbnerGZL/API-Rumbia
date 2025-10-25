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
            print("xdddddddddddd")
            return Response({'detail': 'Credenciales inválidas'}, status=status.HTTP_401_UNAUTHORIZED)

        if not check_password(password, user.password_hash):
            print("2")
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

class UserInfoView(APIView):
    def get(self, request, pk):
        learner = get_object_or_404(User, user_code=pk)
        if learner is None:
            return Response({'error': 'Este usuario no tiene un perfil de aprendiz asociado'}, status=404)
        data = UserSerializer(learner).data
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
        session_data['status'] = "scheduled"
        serializer = SessionSerializer(data=session_data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        
        return Response(serializer.errors, status=400)