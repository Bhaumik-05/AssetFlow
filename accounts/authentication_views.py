from django.contrib.auth import authenticate

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import (
    LoginSerializer,
    LogoutSerializer,
)


class LoginView(APIView):

    permission_classes = []

    def post(self, request):

        serializer = LoginSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = authenticate(
            request,
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"]
        )

        if not user:

            return Response(
                {
                    "message": "Invalid credentials"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "employee": {
                "id": user.id,
                "employee_id": user.employee_id,
                "name": user.first_name + " " + user.last_name,
                "email": user.email,
                "role": user.role,
            }
        })


class LogoutView(APIView):

    def post(self, request):

        serializer = LogoutSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:

            token = RefreshToken(
                serializer.validated_data["refresh"]
            )

            token.blacklist()

            return Response(
                {
                    "message": "Logout successful"
                }
            )

        except TokenError:

            return Response(
                {
                    "message": "Invalid token"
                },
                status=status.HTTP_400_BAD_REQUEST
            )