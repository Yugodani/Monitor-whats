"""
Modelos para o app accounts
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    """
    Modelo de usuário personalizado
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    company = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    is_company_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'company']

    def __str__(self):
        return f"{self.email} - {self.company}"

    def get_full_name(self):
        """Retorna o nome completo do usuário"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email

    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['company']),
        ]


class UserProfile(models.Model):
    """
    Perfil do usuário com informações adicionais
    """
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('manager', 'Gerente'),
        ('user', 'Usuário'),
        ('viewer', 'Visualizador'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # Informações básicas
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)  # Este é o campo que faltava

    # Contato
    alternative_email = models.EmailField(blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)

    # Avatar
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    # Configurações
    max_devices = models.IntegerField(default=5)
    receive_notifications = models.BooleanField(default=True)
    notification_email = models.BooleanField(default=True)

    # Metadados
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Perfil de {self.user.email}"

    class Meta:
        db_table = 'accounts_profile'
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'

class CompanySettings(models.Model):
    """
    Configurações da empresa
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=255, unique=True)

    # Configurações de monitoramento
    max_devices_per_user = models.IntegerField(default=5)
    retention_days = models.IntegerField(default=90, help_text="Dias para manter os dados")

    # Configurações de sincronização
    sync_interval = models.IntegerField(default=300, help_text="Intervalo de sincronização em segundos")
    sync_on_wifi_only = models.BooleanField(default=True)
    sync_on_charge_only = models.BooleanField(default=False)

    # Configurações de monitoramento
    track_calls = models.BooleanField(default=True)
    track_sms = models.BooleanField(default=True)
    track_whatsapp = models.BooleanField(default=True)
    track_deleted_messages = models.BooleanField(default=True)

    # Metadados
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_companies')

    def __str__(self):
        return self.company_name

    class Meta:
        db_table = 'accounts_company_settings'
        verbose_name = 'Configuração da Empresa'
        verbose_name_plural = 'Configurações das Empresas'


class AuditLog(models.Model):
    """
    Log de auditoria para ações importantes
    """
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Criação'),
        ('update', 'Atualização'),
        ('delete', 'Exclusão'),
        ('export', 'Exportação'),
        ('sync', 'Sincronização'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.created_at}"

    class Meta:
        db_table = 'accounts_audit_log'
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['action']),
            models.Index(fields=['created_at']),
        ]