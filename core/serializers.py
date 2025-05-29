from rest_framework import serializers
from .models import GameAudio, Level, Record, User, VerificationCode, Settings, ForgetPasswordCode, SpeakingAudio

from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data, is_active = False)
        instance.set_password(password)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance.set_password(password)
        instance.save()
        return instance
    




    
class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(
        label=_("Email"),
        write_only=True
    )
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(
        label=_("Token"),
        read_only=True
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                                email=email, password=password)
            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs

class VerificationCodeSerializer(serializers.ModelSerializer): # odn't need it
    class Meta:
        model = VerificationCode
        fields = ['code', 'user']
    
    def validate_code(self, value):
        if len(value) != 5:
            raise serializers.ValidationError('Verfication code length must be 5 numbers exactly')
        return value;

    def validate(self, attrs):
        code = attrs['code']
        user_code = VerificationCode.objects.filter(user=attrs['user'])
        if code != user_code:
            raise serializers.ValidationError('incorrect verification code')
        return super().validate(attrs)
    

class ProfilePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['picture']
    
    def upload(self, instance, validated_data):
        instance.picture = validated_data.get('picture', instance.picture)
        instance.save()
        return instance


class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = '__all__'

class ForgetPasswordCodeSerializer(serializers.ModelSerializer): # odn't need it
    class Meta:
        model = VerificationCode
        fields = ['code', 'user']
    
    def validate_code(self, value):
        if len(value) != 5:
            raise serializers.ValidationError('Verfication code length must be 5 numbers exactly')
        return value

    def validate(self, attrs):
        code = attrs['code']
        user_code = VerificationCode.objects.filter(user=attrs['user'])
        if code != user_code:
            raise serializers.ValidationError('incorrect verification code')
        return super().validate(attrs)


class LevelSerializer(serializers.ModelSerializer):
    language_display = serializers.CharField(source='get_language_display', read_only=True) # If you want 'English' instead of 'en'

    class Meta:
        model = Level
        fields = ['id', 'name', 'level', 'language', 'language_display'] # 'level' is your integer field for level number


class RecordSerializer(serializers.ModelSerializer):
    pre_audio_url = serializers.SerializerMethodField()
    correct_audio_url = serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = ['id', 'level', 'text', 'pre_audio_url', 'correct_audio_url', 'order']

    def get_pre_audio_url(self, obj):
        request = self.context.get('request')
        if obj.pre_audio and request:
            return request.build_absolute_uri(obj.pre_audio.url)
        return None

    def get_correct_audio_url(self, obj):
        request = self.context.get('request')
        if obj.correct_audio and request:
            return request.build_absolute_uri(obj.correct_audio.url)
        return None


class GameAudioSerializer(serializers.ModelSerializer):
    audio_url = serializers.SerializerMethodField()

    class Meta:
        model = GameAudio
        fields = ['id', 'user', 'record', 'audio_url', 'attempt_score', 'is_correct', 'created_at']
        read_only_fields = ['user', 'created_at'] # User set from request

    def get_audio_url(self, obj):
        request = self.context.get('request')
        if obj.audio and request:
            return request.build_absolute_uri(obj.audio.url)
        return None

class SpeakingAudioSerializer(serializers.ModelSerializer):
    audio_url = serializers.SerializerMethodField()

    class Meta:
        model = SpeakingAudio
        fields = '__all__'
