from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from main.models import BaseInfo
from .serializers import MeSerializer


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        info = BaseInfo.get_solo()

        data = {
            "company_name": info.name if info else None,
            "username": request.user.username,
            "is_staff": request.user.is_staff,
            "is_superuser": request.user.is_superuser,
            "groups": list(request.user.groups.values_list('name', flat=True)),
        }

        return Response(MeSerializer(data).data)
