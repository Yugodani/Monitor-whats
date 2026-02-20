"""
Views para o app accounts
"""
from rest_framework import viewsets, generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, logout
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend

from .models import User, UserProfile
from .serializers import (
    UserSerializer, UserProfileSerializer, RegisterSerializer,
    LoginSerializer, ChangePasswordSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para visualizar e editar usuários.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['company', 'is_company_admin', 'is_active']
    search_fields = ['email', 'username', 'first_name', 'last_name', 'company']
    ordering_fields = ['date_joined', 'email', 'username']

    def get_permissions(self):
        """
        Permissões personalizadas por ação:
        - Usuários normais só podem ver/editar seu próprio perfil
        - Admins podem ver todos
        """
        if self.action in ['list', 'create', 'destroy']:
            self.permission_classes = [permissions.IsAdminUser]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    def get_queryset(self):
        """
        Filtra queryset baseado no tipo de usuário:
        - Admin vê todos os usuários da empresa
        - Usuário comum vê apenas seu próprio perfil
        """
        user = self.request.user
        if user.is_superuser or user.is_company_admin:
            return User.objects.filter(company=user.company)
        return User.objects.filter(id=user.id)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Retorna o usuário atual
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """
        Faz logout do usuário
        """
        logout(request)
        return Response({'detail': 'Logout realizado com sucesso'})

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Ativa um usuário (apenas admin)
        """
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'status': 'Usuário ativado'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Desativa um usuário (apenas admin)
        """
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'status': 'Usuário desativado'})


class ProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet para visualizar e editar perfis de usuário.
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filtra perfis baseado no tipo de usuário
        """
        user = self.request.user
        if user.is_superuser or user.is_company_admin:
            return UserProfile.objects.filter(user__company=user.company)
        return UserProfile.objects.filter(user=user)

    @action(detail=False, methods=['get', 'put', 'patch'])
    def my_profile(self, request):
        """
        Retorna ou atualiza o perfil do usuário atual
        """
        profile = request.user.profile

        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        else:
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def upload_avatar(self, request, pk=None):
        """
        Upload de avatar para o perfil
        """
        profile = self.get_object()
        avatar_file = request.FILES.get('avatar')

        if avatar_file:
            profile.avatar = avatar_file
            profile.save()
            serializer = self.get_serializer(profile)
            return Response(serializer.data)

        return Response(
            {'error': 'Nenhum arquivo enviado'},
            status=status.HTTP_400_BAD_REQUEST
        )


class RegisterView(generics.CreateAPIView):
    """
    View para registro de novos usuários
    """
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Create user profile
        UserProfile.objects.create(user=user)

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """
    View para visualizar e editar o usuário atual
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class ChangePasswordView(APIView):
    """
    View para alterar a senha do usuário
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'old_password': 'Senha atual incorreta'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({'detail': 'Senha alterada com sucesso'})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """
    View para login de usuários
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = authenticate(
        email=serializer.validated_data['email'],
        password=serializer.validated_data['password']
    )

    if not user:
        return Response(
            {'error': 'Credenciais inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'error': 'Usuário inativo'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    refresh = RefreshToken.for_user(user)

    return Response({
        'user': UserSerializer(user).data,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    View para logout de usuários
    """
    logout(request)
    return Response({'detail': 'Logout realizado com sucesso'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_statistics(request):
    """
    Estatísticas de usuários (apenas admin)
    """
    user = request.user

    if not (user.is_superuser or user.is_company_admin):
        return Response(
            {'error': 'Permissão negada'},
            status=status.HTTP_403_FORBIDDEN
        )

    total_users = User.objects.filter(company=user.company).count()
    active_users = User.objects.filter(company=user.company, is_active=True).count()
    inactive_users = total_users - active_users
    admins = User.objects.filter(company=user.company, is_company_admin=True).count()

    return Response({
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'admins': admins,
        'company': user.company
    })