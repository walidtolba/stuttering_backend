from django.db import models
from django.contrib.auth.models import AbstractUser
from . import managers
import os

class User(AbstractUser):
    def get_upload_to(self, filename):
        return os.path.join('images', 'profile_pictures', str(self.pk), filename)
    
    DEFAULT_PICTURE = 'images/profile_pictures/default_profile_picture.jpg'

    email = models.EmailField(unique=True, max_length=254, verbose_name='email address')
    password = models.CharField(max_length=128, verbose_name='password')
    full_name = models.CharField(max_length=256, verbose_name='full name')
    is_verified = models.BooleanField(default=False)
    picture = models.ImageField(upload_to=get_upload_to, default=DEFAULT_PICTURE)
    username = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = managers.UserManager()

class VerificationCode(models.Model):
    code = models.CharField(max_length=6)
    creationDate = models.DateTimeField(auto_now_add=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.user.email

class Settings(models.Model):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('fr', 'French'),
        ('ar', 'Arabic'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email_notification = models.BooleanField(default=False)
    dark_mode = models.BooleanField(default=False)
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    
    
    def __str__(self):
        return f"Settings for {self.user.email}"
    
class Level(models.Model):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('fr', 'French'),
        ('ar', 'Arabic'),
    ]
    name = models.CharField(max_length=50)
    level = models.IntegerField(default=1, unique=True) # Ensure level numbers are unique
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')

    class Meta:
        ordering = ['language', 'level'] # Order by language then level number

    def __str__(self):
        return f"Level {self.level} - {self.name} ({self.language.upper()})"

class Record(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='records')
    pre_audio = models.FileField(upload_to='audio/pre_audio/') # More specific path
    text = models.TextField()
    correct_audio = models.FileField(upload_to='audio/correct_audio/') # More specific path
    order = models.PositiveIntegerField(default=0) # To define sequence within a level

    class Meta:
        ordering = ['level', 'order'] # Ensure records are ordered within a level

    def __str__(self):
        return f"Record {self.order} for {str(self.level)}"

class LevelInstance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='level_instances')
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    # New field to track the last completed record's order in this level
    last_completed_record_order = models.IntegerField(default=-1) # -1 means no records completed yet
    is_completed = models.BooleanField(default=False) # If the level itself is completed

    class Meta:
        unique_together = ('user', 'level') # User can only have one instance per level

    def __str__(self):
        return f"{self.user.username} - {str(self.level)} - Score: {self.score}"

class GameAudio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) # Who submitted this audio
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='game_audios')
    audio = models.FileField(upload_to='audio/game_audio/') # User's submitted audio
    attempt_score = models.IntegerField(default=0) # Score for this specific attempt
    is_correct = models.BooleanField(default=False) # Was this attempt deemed correct?
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Audio by {self.user.username} for {str(self.record)}"
        return f"Audio for Level {self.record.level.level}"



class ForgetPasswordCode(models.Model):
    code = models.CharField(max_length=6)
    creationDate = models.DateTimeField(auto_now_add=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.user.email


class SpeakingAudio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    audio = models.FileField(upload_to='audio/speaking_audio/')
    created_at = models.DateTimeField(auto_now_add=True)
    no_stutter = models.FloatField(default=0.0)  # Percentage of fluency
    prolongation = models.FloatField(default=0.0)  # Percentage of elongation
    repetition = models.FloatField(default=0.0)  # Percentage of repetition
    block = models.FloatField(default=0.0)  # Percentage of blocking

    def __str__(self):
        return f"Speaking Audio by {self.user.email} at {self.created_at}"