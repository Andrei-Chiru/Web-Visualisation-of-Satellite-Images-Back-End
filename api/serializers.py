from django.contrib.auth.models import User
from rest_framework import serializers

# the serializer class is used to convert complex data types into native python data types that can be rendered into JSON, XML or other content types

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True, 'required': True}} # password is write only and required

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user






