from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import UserViewset, Signup
from rest_framework_jwt.views import obtain_jwt_token, verify_jwt_token

router = DefaultRouter()
router.register(r'users', UserViewset)
urlpatterns = [
    path('', include(router.urls)),
    path('signup/', Signup.as_view(), name='Signup'),
    path('signin/', obtain_jwt_token, name='Signin'),
    path('token-verify/', verify_jwt_token, name='TokenVerify')
]
