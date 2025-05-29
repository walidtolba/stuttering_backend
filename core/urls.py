from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.Login.as_view()),
    path('signup/', views.SignupView.as_view()),
    path('resend_code/', views.ResendVerificationCode.as_view()),
    path('verify_signup/', views.SignupVerificationView.as_view()),
    path('my_profile/', views.MyProfileView.as_view()),
    path('profile_picture/<int:id>/', views.FetchProfilePictureView.as_view()),
    path('change_profile_picture/', views.ChangeProfilePictureView.as_view()),
    path('change_email/', views.ChangeEmailView.as_view()),
    path('change_password/',views.ChangePasswordView.as_view()),
    path('change_name/', views.ChangeNameView.as_view()),
    path('settings/', views.SettingsView.as_view()),
    path('statistics/', views.StatisticsView.as_view()),
    path('current_state/', views.CurrentGameStateAPIView.as_view(), name='current_game_state'),
    path('submit_audio/', views.SubmitGameAudioAPIView.as_view(), name='submit_game_audio'),
    path('reset_password/', views.ForgetPasswordView.as_view()),
    path('verify_reset_password/', views.ForgetPasswordVerificationView.as_view()),
    path('audio_chunk_upload/', views.AudioChunkUpload.as_view(), name='audio_chunk_upload'),
]