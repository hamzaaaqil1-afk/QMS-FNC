from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
@permission_classes([AllowAny])
def get_csrf(request):
    token = get_token(request)
    return Response({'csrfToken': token})


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'erreur': 'Username et password requis'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Si l'identifiant contient @, chercher par email
    if '@' in username:
        try:
            from django.contrib.auth.models import User
            user_obj = User.objects.get(email=username)
            username = user_obj.username
        except User.DoesNotExist:
            return Response(
                {'erreur': 'Identifiants incorrects'},
                status=status.HTTP_401_UNAUTHORIZED
            )

    user = authenticate(request=request, username=username, password=password)

    if user is None:
        return Response(
            {'erreur': 'Identifiants incorrects'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    login(request, user)
    return Response({
        'message': 'Connexion réussie',
        'user': {
            'id':        user.id,
            'username':  user.username,
            'email':     user.email,
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'is_admin':  user.is_superuser,
        }
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    logout(request)
    return Response({'message': 'Déconnexion réussie'})


@api_view(['GET'])
@permission_classes([AllowAny])
def me_view(request):
    if not request.user.is_authenticated:
        return Response(
            {'erreur': 'Non authentifié'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    return Response({
        'id':        request.user.id,
        'username':  request.user.username,
        'email':     request.user.email,
        'full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
        'is_admin':  request.user.is_superuser,
    })
    
