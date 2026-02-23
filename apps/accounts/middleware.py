from django.db import connection
from django.shortcuts import redirect
from django.urls import reverse


class MultiTenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Set tenant schema for authenticated users
            schema_name = request.user.company.lower().replace(' ', '_').replace('-', '_')
            connection.set_tenant(schema_name)

        response = self.get_response(request)
        return response
