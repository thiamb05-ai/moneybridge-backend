views = open('accounts/views.py').read()

register = '''
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
        return Response({"error": "Cet email est déjà utilisé"}, status=400)

    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )
    refresh = RefreshToken.for_user(user)
    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {"email": user.email, "name": user.get_full_name()}
    })
'''

with open('accounts/views.py', 'a') as f:
    f.write(register)
print('OK')