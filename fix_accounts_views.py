content = open('accounts/views.py').read()
print(repr(content))

views = '''from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User

@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get("email")
    password = request.data.get("password")
    user = authenticate(username=email, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {"email": user.email, "name": user.get_full_name()}
        })
    return Response({"error": "Identifiants incorrects"}, status=400)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile(request):
    user = request.user
    return Response({
        "email": user.email,
        "name": user.get_full_name(),
    })
'''

with open('accounts/views.py', 'w') as f:
    f.write(views)
print('accounts/views.py OK')