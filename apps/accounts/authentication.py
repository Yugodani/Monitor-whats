from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from django.db import connection


class MultiTenantJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)

        # Set tenant schema based on user's company
        user = self.get_user(validated_token)
        if user and user.company:
            # Create schema name from company (lowercase, no spaces)
            schema_name = user.company.lower().replace(' ', '_').replace('-', '_')
            connection.set_tenant(schema_name)

        return (user, validated_token)