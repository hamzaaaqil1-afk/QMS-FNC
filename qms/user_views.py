from django.contrib.auth.models import User, Group
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import serializers, status


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Group
        fields = ['id', 'name']


class UserManageSerializer(serializers.ModelSerializer):
    roles     = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    password  = serializers.CharField(write_only=True, required=False)

    class Meta:
        model  = User
        fields = [
            'id', 'username', 'email',
            'first_name', 'last_name', 'full_name',
            'is_active', 'is_superuser',
            'roles', 'password',
            'date_joined', 'last_login',
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

    def get_roles(self, obj):
        return [g.name for g in obj.groups.all()]

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        roles    = self.initial_data.get('roles', [])
        user     = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        groups = Group.objects.filter(name__in=roles)
        user.groups.set(groups)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        roles    = self.initial_data.get('roles', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if password:
            instance.set_password(password)
        instance.save()
        if roles is not None:
            groups = Group.objects.filter(name__in=roles)
            instance.groups.set(groups)
        return instance


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_utilisateurs(request):
    users = User.objects.prefetch_related('groups').order_by('first_name', 'last_name')
    serializer = UserManageSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def creer_utilisateur(request):
    serializer = UserManageSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(UserManageSerializer(user).data, status=201)
    return Response(serializer.errors, status=400)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def modifier_utilisateur(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'erreur': 'Utilisateur introuvable'}, status=404)
    serializer = UserManageSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        user = serializer.save()
        return Response(UserManageSerializer(user).data)
    return Response(serializer.errors, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_actif(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'erreur': 'Utilisateur introuvable'}, status=404)
    user.is_active = not user.is_active
    user.save()
    return Response({'is_active': user.is_active})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_groupes(request):
    groups = Group.objects.all().order_by('name')
    serializer = GroupSerializer(groups, many=True)
    return Response(serializer.data)