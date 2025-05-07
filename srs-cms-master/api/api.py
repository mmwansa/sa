from ninja import NinjaAPI
from django.contrib.auth import authenticate, login, logout
from ninja.security import django_auth
from ninja import Schema

api = NinjaAPI(csrf=True)


class AuthSchema(Schema):
    username: str
    password: str


@api.post("/auth/login")
def login_view(request, payload: AuthSchema):
    user = authenticate(request, username=payload.username, password=payload.password)
    if user is not None:
        login(request, user)
        return {"success": True, "message": "Logged in successfully."}
    else:
        return {"success": False, "message": "Invalid credentials."}


@api.post("/auth/logout")
def logout_view(request):
    logout(request)
    return {"success": True, "message": "Logged out successfully."}


@api.get("/auth/user")
def get_user(request):
    if request.user.is_authenticated:
        return {
            "is_authenticated": True,
            "username": request.user.username,
            "email": request.user.email,
        }
    else:
        return {"is_authenticated": False}


@api.get("/hello", auth=django_auth)
def test_protected(request):
    """
    Test endpoint that requires authentication.
    TODO: Delete this later.
    """
    if request.user.is_authenticated:
        return {"message": f"Hello, {request.user.username}!"}
    else:
        return {"message": "You are not authenticated."}
