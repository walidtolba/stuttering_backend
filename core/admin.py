from django.contrib import admin
from .models import User, VerificationCode, Settings, ForgetPasswordCode, Level, GameAudio, Record, LevelInstance


admin.site.register(User)
admin.site.register(VerificationCode)
admin.site.register(Settings)
admin.site.register(ForgetPasswordCode)
admin.site.register(Level)
admin.site.register(GameAudio)
admin.site.register(Record)
admin.site.register(LevelInstance)
