content = '''from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()

@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get("email")
    password = request.data.get("password")
    try:
        user = User.objects.get(email=email)
        if user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {"email": user.email, "name": user.get_full_name()}
            })
    except User.DoesNotExist:
        pass
    return Response({"error": "Identifiants incorrects"}, status=400)

@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    email = request.data.get("email")
    password = request.data.get("password")
    first_name = request.data.get("first_name", "")
    last_name = request.data.get("last_name", "")
    if not email or not password:
        return Response({"error": "Email et mot de passe requis"}, status=400)
    if User.objects.filter(email=email).exists():
        return Response({"error": "Cet email est deja utilise"}, status=400)
    user = User.objects.create_user(
        username=email, email=email, password=password,
        first_name=first_name, last_name=last_name
    )
    refresh = RefreshToken.for_user(user)
    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {"email": user.email, "name": user.get_full_name()}
    })

@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def profile(request):
    user = request.user
    if request.method == "PATCH":
        user.first_name = request.data.get("first_name", user.first_name)
        user.last_name = request.data.get("last_name", user.last_name)
        user.save()
    return Response({
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "name": user.get_full_name(),
        "date_joined": user.date_joined,
    })
'''

with open('accounts/views.py', 'w') as f:
    f.write(content)
print('OK')