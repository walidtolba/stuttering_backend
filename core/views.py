from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser
from django.http import HttpResponse
from django.conf import settings
from rest_framework import parsers, renderers, status

from .serializers import AuthTokenSerializer, LevelSerializer, SettingSerializer
from .serializers import UserSerializer, ProfilePictureSerializer
import jwt, datetime
from .models import ForgetPasswordCode, GameAudio, Level, LevelInstance, Record, Settings, User, VerificationCode
import random
from django.core.mail import send_mail
from .custom_renderers import AudioRenderer, ImageRenderer
from rest_framework import generics
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from django.db.models import Sum, Max, Count



class Login(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer

    def post(self, request):
        print(request.data)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            token = jwt.encode({
                'email': serializer.validated_data['email'],
                'iat': datetime.datetime.utcnow(),
                'nbf': datetime.datetime.utcnow() + datetime.timedelta(minutes=-5),
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=5)
            }, settings.SECRET_KEY, algorithm='HS256')
            user = User.objects.filter(email=serializer.validated_data['email']).first()
            return Response({'token': token, "is_verified": user.is_verified})
        user = User.objects.filter(email=request.data['email']).first()
        if user:
            if not user.is_active:
                return Response({'error': 'You need to verify your email'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SignupView(APIView): 
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
        print(serializer.errors)
        code = ''.join([str(random.choice(range(10))) for i in range(6)])
        verificationCode = VerificationCode(code=code, user=instance)
        verificationCode.save()
        data = serializer.validated_data
        subject = f'welcome to {settings.APP_NAME}'
        message = f'Hi {data["full_name"]} , thank you for registering in {settings.APP_NAME}, your verification code is: {code}'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = (data['email'],)
        html_message = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <p>Hi <strong>{data["full_name"]}</strong>,</p>
        <p>Thank you for registering in <strong>{settings.APP_NAME}</strong>!</p>
        <p>Your verification code is:</p>
        <div style="font-size: 24px; font-weight: bold; color: #2c3e50; margin: 10px 0;">
          {code}
        </div>
        <p>Please enter this code to verify your email address.</p>
        <br>
        <p style="font-size: 12px; color: gray;">If you didn’t request this, you can ignore this email.</p>
      </body>
    </html>
    """

        send_mail( subject, message, email_from, recipient_list, html_message=html_message, fail_silently=False)
        return Response({'email': data['email'], "message": 'A verification code has been sent to your email'}, status=200)

class ResendVerificationCode(APIView): 
    def post(self, request):
        user = User.objects.filter(email=request.data.get('email')).first()
        if not user:
            return Response({'error': 'There is no user with such email'}, status=400)
        if user.is_verified:
            return Response({'error': 'The Email is already verified'}, status=400)
        old_verification_code = VerificationCode.objects.filter(user=user)
        for code in old_verification_code:
            code.delete()
        code = ''.join([str(random.choice(range(10))) for i in range(6)])
        verificationCode = VerificationCode(code=code, user=user)
        verificationCode.save()
        subject = 'welcome to HomeCare'
        message = f'Hi {user.first_name} {user.last_name} , thank you for registering in HomeCare, your verification code is: {code}'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = (user.email,)
        html_message = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <p>Hi <strong>{user.first_name} {user.last_name}</strong>,</p>
        <p>Thank you for registering in <strong>{settings.APP_NAME}</strong>!</p>
        <p>Your verification code is:</p>
        <div style="font-size: 24px; font-weight: bold; color: #2c3e50; margin: 10px 0;">
          {code}
        </div>
        <p>Please enter this code to verify your email address.</p>
        <br>
        <p style="font-size: 12px; color: gray;">If you didn’t request this, you can ignore this email.</p>
      </body>
    </html>
    """

        send_mail( subject, message, email_from, recipient_list, html_message=html_message, fail_silently=False)
        return Response({'email': user.email, "message": 'A verification code has been sent to your email'}, status=200)

class SignupVerificationView(APIView):  
    def post(self, request):
        code = request.data['code'] 
        user = User.objects.filter(email=request.data['email']).first()
        user_code = VerificationCode.objects.filter(user=user.id).first()   
        if code == user_code.code:
            user_code.delete()
            user.is_verified = True
            Settings(user=user).save()
            user.save()
            return Response({'email': user.email, 'message': 'Your email has been verified'}, status=200)
        return Response({'error': 'Can\'t verify user'}, status=400)


class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        user_data = UserSerializer(instance=user).data
        data = dict(user_data)
        print(data)
        return Response(data=data)
    
class ChangeProfilePictureView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser, MultiPartParser]
    
    def post(self, request):
        user = request.user
        serializer = ProfilePictureSerializer(instance=user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(data={'message': 'Profile picture changed successfully'}, status=200)
        return Response(data=serializer.errors, status=400)

class OtherProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, id):
        user = User.objects.filter(id=id).first()
        user_data = UserSerializer(instance=user).data
        user_data.pop('password')
        data = dict(user_data)
        return Response(data=data)

class FetchProfilePictureView(generics.RetrieveAPIView):
    renderers_classes = [ImageRenderer]
    def get(self, request, id):
        data = User.objects.get(id=id).picture
        return HttpResponse(data, content_type='image/' + data.path.split(".")[-1])

class ChangeEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        new_email = request.data.get('email')
        
        if not new_email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_email(new_email)
        except ValidationError:
            return Response({'error': 'Invalid email format.'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=new_email).exists():
            return Response({'error': 'This email is already in use.'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.email = new_email
        user.is_verfied = False
        user.save()

        return Response({'message': 'Email updated successfully.'}, status=status.HTTP_200_OK)

class ChangeNameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        new_full_name = request.data.get('full_name')

        if not new_full_name:
            return Response({'error': 'Full name is required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.full_name = new_full_name
        user.save()

        return Response({'message': 'Name updated successfully.'}, status=status.HTTP_200_OK)
    

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        if not old_password or not new_password:
            return Response({'error': 'Both old and new passwords are required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        print(user)
        if not user.check_password(old_password):
            return Response({'error': 'Old password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            print(e.messages)
            return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)

class SettingsView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        print('hi')
        try:
            settings = request.user.settings
        except Settings.DoesNotExist:
            Settings(user=request.user).save()
            settings = request.user.settings
            
        serializer = SettingSerializer(settings, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Settings updated successfully.', ** serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        try:
            settings = request.user.settings
        except Settings.DoesNotExist:
            Settings(user=request.user).save()
            settings = request.user.settings
        serializer = SettingSerializer(instance=settings)
        return Response(serializer.data)


class ForgetPasswordView(APIView): 
    def post(self, request):
        email = request.data.get('email')
        print('niggas')
        if not email:
            return Response({'error': 'Email is required'}, status=400)
        try:
            validate_email(email)
        except ValidationError:
            return Response({'error': 'Invalid email format'}, status=400)
        if not User.objects.filter(email=email).exists():
            return Response({'error': 'There is no user with such email'}, status=400)
        user = User.objects.get(email=email)
        code = ''.join([str(random.choice(range(10))) for i in range(6)])
        if ForgetPasswordCode.objects.filter(user=user).exists():
            for old_code in ForgetPasswordCode.objects.filter(user=user):
                old_code.delete()
        forget_password_code = ForgetPasswordCode(code=code, user=user)
        forget_password_code.save()
        subject = f'welcome to {settings.APP_NAME}'
        message = f'Hi {user.first_name} {user.last_name} , We received a request to reset your password for <strong>{settings.APP_NAME}, your password reset code is: {code}'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = (user.email,)
        html_message = f"""
    <html>
  <body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <p>Hi <strong>{user.first_name} {user.last_name}</strong>,</p>
    <p>We received a request to reset your password for <strong>{settings.APP_NAME}</strong>.</p>
    <p>Your password reset code is:</p>
    <div style="font-size: 24px; font-weight: bold; color: #2c3e50; margin: 10px 0;">
      {code}
    </div>
    <p>Please enter this code to reset your password.</p>
    <br>
    <p style="font-size: 12px; color: gray;">If you didn’t request a password reset, you can safely ignore this email.</p>
  </body>
</html>
    """

        send_mail( subject, message, email_from, recipient_list, html_message=html_message, fail_silently=False)
        return Response({'email': user.email, "message": 'A verification code has been sent to your email'}, status=200)

class ForgetPasswordVerificationView(APIView):  
    def post(self, request):
        code = request.data.get('code')
        if not code:
            return Response({'error': 'Code is required'}, status=400)
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=400)
        try:
            validate_email(email)
        except ValidationError:
            return Response({'error': 'Invalid email format'}, status=400)
        if not User.objects.filter(email=email).exists():
            return Response({'error': 'There is no user with such email'}, status=400)
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'error': 'There is no user with such email'}, status=400)
        user_code = ForgetPasswordCode.objects.filter(user=user.id).first()
        if user_code is None:
            return Response({'error': 'There is no verification code for this user'}, status=400)
        password = request.data.get('password')
        if not password:
            return Response({'error': 'Password is required'}, status=400)
        try:
            validate_password(password, user=user)
        except ValidationError as e:
            return Response({'error': e.messages}, status=400)
        if code == user_code.code:
            user.set_password(password)
            user.save()
            user_code.delete()
            return Response({'email': user.email, 'message': 'Your password has been changed'}, status=200)
        return Response({'error': 'Can\'t verify code'}, status=400)
    
    def put(self, request):
        code = request.data.get('code')
        if not code:
            return Response({'error': 'Code is required'}, status=400)
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=400)
        try:
            validate_email(email)
        except ValidationError:
            return Response({'error': 'Invalid email format'}, status=400)
        if not User.objects.filter(email=email).exists():
            return Response({'error': 'There is no user with such email'}, status=400)
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'error': 'There is no user with such email'}, status=400)
        user_code = ForgetPasswordCode.objects.filter(user=user.id).first()
        if user_code is None:
            return Response({'error': 'There is no verification code for this user'}, status=400)
        
        if code == user_code.code:
            return Response({'email': user.email, 'message': 'The code you entered is valid'}, status=200)
        return Response({'error': 'Can\'t verify code'}, status=400)



class StatisticsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response({
            'message': 'Statistics page'
        }, status=200)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser
from django.utils import timezone
from .models import SpeakingAudio
from .serializers import SpeakingAudioSerializer
import os

class AudioChunkUpload(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser, MultiPartParser]

    def post(self, request):
        audio_chunk = request.data.get('audio_chunk')
        created_at_str = request.data.get('created_at')
        

        if not audio_chunk or not created_at_str:
            return Response({'error': 'Missing audio_chunk or created_at'}, status=400)

        try:
            created_at = timezone.datetime.fromisoformat(created_at_str)
        except ValueError:
            return Response({'error': 'Invalid created_at format.'}, status=400)

        # Try to find recent existing record for this user
        audio_record = SpeakingAudio.objects.filter(
            user=request.user,
            created_at__date=created_at.date()
        ).order_by('-created_at').first()

        if audio_record and abs((audio_record.created_at - created_at).total_seconds()) <= 10:
            # Append to existing audio file
            with open(audio_record.audio.path, 'ab') as f:
                for chunk in audio_chunk.chunks():
                    f.write(chunk)
            instance = audio_record
        else:
            # Create new record
            data = {
                'user': request.user.id,
                'audio': audio_chunk,
                'created_at': created_at_str,
            }
            print(data)
            serializer = SpeakingAudioSerializer(data=data)
            if serializer.is_valid():
                instance = serializer.save()
            else:
                return Response(serializer.errors, status=400)

        return Response({'message': 'Audio saved', 'id': instance.id}, status=200)



def get_or_create_level_instance(user, level):
    instance, created = LevelInstance.objects.get_or_create(
        user=user,
        level=level,
        defaults={'last_completed_record_order': -1} # Start with no records completed
    )
    return instance

class CurrentGameStateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Determine user's language preference (e.g., from UserProfile or a setting)
        # For now, let's assume a default or the user's first level language
        user_language = user.profile.language_preference if hasattr(user, 'profile') else 'en' # Example

        # --- 1. Find the user's current or last played level instance ---
        last_played_level_instance = LevelInstance.objects.filter(user=user, level__language=user_language) \
                                                            .select_related('level') \
                                                            .order_by('-level__level') \
                                                            .first()

        current_level_obj = None
        level_instance = None

        if last_played_level_instance and not last_played_level_instance.is_completed:
            level_instance = last_played_level_instance
            current_level_obj = level_instance.level
        else:
            # Find the next uncompleted or unstarted level for the user's language
            completed_level_ids = LevelInstance.objects.filter(user=user, is_completed=True, level__language=user_language).values_list('level_id', flat=True)
            
            next_level_to_start = Level.objects.filter(language=user_language) \
                                          .exclude(id__in=completed_level_ids) \
                                          .order_by('level') \
                                          .first()
            if next_level_to_start:
                current_level_obj = next_level_to_start
                level_instance = get_or_create_level_instance(user, current_level_obj)
            else:
                # All levels for this language might be completed
                if last_played_level_instance and last_played_level_instance.is_completed:
                    # User has completed all levels they've played. Check if truly all levels are done.
                    total_levels_for_language = Level.objects.filter(language=user_language).count()
                    if len(completed_level_ids) >= total_levels_for_language:
                         return Response({
                            "user_id": user.id,
                            "username": user.username,
                            "total_score": user.level_instances.aggregate(total=Sum('score'))['total'] or 0,
                            "current_level": LevelSerializer(last_played_level_instance.level, context={'request': request}).data if last_played_level_instance else None,
                            "level_progress": {"records_completed": 0, "total_records_in_level": 0, "percentage": 100.0 } if last_played_level_instance else None, # Or specific completed progress
                            "next_record_to_play": None,
                            "is_game_completed": True
                        })

                # No levels available or something went wrong
                return Response({"detail": "No active game or all levels completed."}, status=404)


        # --- 2. Determine the next record to play in the current level ---
        # The next record's order is last_completed_record_order + 1
        next_record_order = level_instance.last_completed_record_order + 1
        next_record = Record.objects.filter(level=current_level_obj, order=next_record_order).first()

        # --- 3. Calculate total score ---
        total_score = user.level_instances.aggregate(total=Sum('score'))['total'] or 0

        # --- 4. Calculate level progress ---
        total_records_in_level = current_level_obj.records.count()
        records_completed_in_level = level_instance.last_completed_record_order + 1 # since order is 0-indexed
        
        # Ensure records_completed_in_level doesn't exceed total_records_in_level if level is completed
        if level_instance.is_completed:
            records_completed_in_level = total_records_in_level
        
        level_percentage = (records_completed_in_level / total_records_in_level * 100) if total_records_in_level > 0 else 0.0
        if level_instance.is_completed and not next_record : # If level completed and no next record, progress is 100%
             level_percentage = 100.0


        # Prepare data for next_record_to_play
        next_record_data = None
        if next_record:
            next_record_data = {
                "id": next_record.id,
                "text": next_record.text,
                "pre_audio_url": request.build_absolute_uri(next_record.pre_audio.url) if next_record.pre_audio else None,
                "order": next_record.order
            }
        elif level_instance.is_completed: # Current level done, but maybe there's another level
             pass # Handled by the is_game_completed logic next

        # Check if all levels for the language are completed
        is_game_completed = False
        if not next_record_data and level_instance.is_completed:
            all_levels_for_lang_count = Level.objects.filter(language=user_language).count()
            user_completed_levels_count = LevelInstance.objects.filter(user=user, level__language=user_language, is_completed=True).count()
            if user_completed_levels_count >= all_levels_for_lang_count:
                is_game_completed = True


        return Response({
            "user_id": user.id,
            "username": user.username,
            "total_score": total_score,
            "current_level": LevelSerializer(current_level_obj, context={'request': request}).data,
            "level_progress": {
                "records_completed": records_completed_in_level,
                "total_records_in_level": total_records_in_level,
                "percentage": round(level_percentage, 2)
            },
            "next_record_to_play": next_record_data,
            "is_game_completed": is_game_completed
        })




# This is a placeholder for your actual audio processing and scoring logic
def evaluate_user_audio(user_audio_path, correct_text, correct_audio_path):
    # In a real app, this would involve:
    # 1. Speech-to-text on user_audio_path.
    # 2. Comparison of transcribed text with correct_text (e.g., Levenshtein distance).
    # 3. Potentially pronunciation scoring using AI/ML services.
    # 4. Determining a score and if it's "correct".
    print(f"Simulating evaluation for: {user_audio_path} against {correct_text}")
    import random
    is_correct_attempt = random.choice([True, True, False]) # Simulate 2/3 chance of being correct
    score = random.randint(70, 100) if is_correct_attempt else random.randint(30, 60)
    feedback_msg = "Good job!" if is_correct_attempt else "Try again, focus on the 'th' sound."
    return {"is_correct": is_correct_attempt, "score": score, "feedback": feedback_msg}


class SubmitGameAudioAPIView(APIView):
    permission_classes = [IsAuthenticated]
    # parser_classes = [MultiPartParser, FormParser] # DRF handles this by default for file uploads

    def post(self, request):
        user = request.user
        record_id = request.data.get('record_id')
        audio_file = request.FILES.get('audio_file')

        if not record_id:
            return Response({"record_id": ["This field is required."]}, status=400)
        if not audio_file:
            return Response({"audio_file": ["No file was submitted."]}, status=400)

        try:
            record_id = int(record_id)
            current_record = get_object_or_404(Record.objects.select_related('level'), pk=record_id)
        except ValueError:
            return Response({"record_id": ["Invalid record ID format."]}, status=400)
        except Record.DoesNotExist: # Covered by get_object_or_404
             return Response({"detail": "Record not found."}, status=404)


        # --- 1. Save the user's submitted audio ---
        game_audio = GameAudio.objects.create(
            user=user,
            record=current_record,
            audio=audio_file
        )

        # --- 2. Evaluate the audio (placeholder) ---
        # In a real app, user_audio_file.temporary_file_path() or game_audio.audio.path can be used
        evaluation_result = evaluate_user_audio(
            game_audio.audio.path,
            current_record.text,
            current_record.correct_audio.path
        )

        game_audio.attempt_score = evaluation_result['score']
        game_audio.is_correct = evaluation_result['is_correct']
        game_audio.save()

        # --- 3. Update LevelInstance score and progress ---
        level_instance = get_or_create_level_instance(user, current_record.level)
        
        next_action_status = "retry_current_record"
        next_action_message = evaluation_result['feedback']
        next_record_to_play_data = None
        next_level_info_data = None

        if game_audio.is_correct:
            level_instance.score += game_audio.attempt_score # Add attempt score to level score
            # Update last_completed_record_order if this record's order is higher
            if current_record.order > level_instance.last_completed_record_order:
                 level_instance.last_completed_record_order = current_record.order
            
            next_action_message = f"Correct! {evaluation_result['feedback']}"

            # Check for next record in the same level
            next_record_in_level = Record.objects.filter(
                level=current_record.level,
                order=current_record.order + 1
            ).first()

            if next_record_in_level:
                next_action_status = "proceed_next_record"
                next_record_to_play_data = {
                    "id": next_record_in_level.id,
                    "text": next_record_in_level.text,
                    "pre_audio_url": request.build_absolute_uri(next_record_in_level.pre_audio.url) if next_record_in_level.pre_audio else None,
                    "order": next_record_in_level.order,
                    "level_id": current_record.level.id
                }
            else:
                # Last record of the current level completed
                level_instance.is_completed = True
                next_action_message = f"Level {current_record.level.level_number} completed! {evaluation_result['feedback']}"
                
                # Check for next level
                next_level_obj = Level.objects.filter(
                    language=current_record.level.language,
                    level=current_record.level.level + 1 # Assuming level numbers are sequential integers
                ).first()

                if next_level_obj:
                    next_action_status = "proceed_next_level"
                    # Get or create instance for the new level
                    get_or_create_level_instance(user, next_level_obj) # Ensure it exists

                    first_record_of_next_level = Record.objects.filter(level=next_level_obj, order=0).first()
                    if first_record_of_next_level:
                         next_record_to_play_data = {
                            "id": first_record_of_next_level.id,
                            "text": first_record_of_next_level.text,
                            "pre_audio_url": request.build_absolute_uri(first_record_of_next_level.pre_audio.url) if first_record_of_next_level.pre_audio else None,
                            "order": first_record_of_next_level.order,
                            "level_id": next_level_obj.id
                        }
                    next_level_info_data = LevelSerializer(next_level_obj, context={'request': request}).data

                else:
                    # No next level, game for this language might be completed
                    next_action_status = "level_completed_no_next_level" # Or "game_completed" if truly all levels
                    # Check if all levels for the language are completed
                    all_levels_for_lang_count = Level.objects.filter(language=current_record.level.language).count()
                    user_completed_levels_count = LevelInstance.objects.filter(user=user, level__language=current_record.level.language, is_completed=True).count()
                    if user_completed_levels_count >= all_levels_for_lang_count:
                        next_action_status = "game_completed"


        level_instance.save() # Save changes to score, last_completed_record_order, is_completed

        return Response({
            "attempt_id": game_audio.id,
            "record_id": current_record.id,
            "evaluation": {
                "is_correct": game_audio.is_correct,
                "score_awarded": game_audio.attempt_score,
                "feedback": evaluation_result['feedback'] # Feedback from evaluation
            },
            "correct_audio_url": request.build_absolute_uri(current_record.correct_audio.url) if current_record.correct_audio else None,
            "user_level_score_updated_to": level_instance.score,
            "next_action": {
                "status": next_action_status,
                "message": next_action_message,
                "next_record_to_play": next_record_to_play_data,
                "next_level_info": next_level_info_data
            }
        })
        

class FetchAudioFile(generics.RetrieveAPIView):
    renderers_classes = [AudioRenderer]
    def get(self, request, id):
        data = User.objects.get(id=id).audio
        return HttpResponse(data, content_type='audio/' + data.path.split(".")[-1])