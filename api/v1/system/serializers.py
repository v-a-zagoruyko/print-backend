from rest_framework import serializers


class MeSerializer(serializers.Serializer):
    company_name = serializers.CharField()
    username = serializers.CharField()
    is_staff = serializers.BooleanField()
    is_superuser = serializers.BooleanField()
    groups = serializers.ListField(child=serializers.CharField())
