import os
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Level, Record # Adjust 'game.models' to your app's name

# --- Configuration ---
# Relative path from MEDIA_ROOT to your dummy audio file
DUMMY_AUDIO_FILE_PATH_RELATIVE = 'placeholder.mp3'
# If you don't have a dummy file and just want to store paths:
# DUMMY_AUDIO_FILE_PATH_RELATIVE = 'audio/placeholder/placeholder.mp3' # This file won't exist

class Command(BaseCommand):
    help = 'Populates the database with 10 levels, each having 10 records, for testing purposes.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to populate levels and records...'))

        # Ensure the dummy audio file path is valid if you are using an actual file
        # For FileField, Django expects the path relative to MEDIA_ROOT when assigning directly
        # to the field.
        dummy_audio_full_path = os.path.join(settings.MEDIA_ROOT, DUMMY_AUDIO_FILE_PATH_RELATIVE)

        if not DUMMY_AUDIO_FILE_PATH_RELATIVE.endswith('placeholder.mp3'): # Skip check if using placeholder path
            # Create dummy directories if they don't exist
            dummy_audio_dir = os.path.dirname(dummy_audio_full_path)
            if not os.path.exists(dummy_audio_dir):
                os.makedirs(dummy_audio_dir)
                self.stdout.write(self.style.WARNING(f"Created directory: {dummy_audio_dir}"))

            # Create a dummy file if it doesn't exist (simplistic approach)
            if not os.path.exists(dummy_audio_full_path):
                try:
                    with open(dummy_audio_full_path, 'wb') as f: # 'wb' for binary, good for audio
                        f.write(b'dummy content') # Minimal content
                    self.stdout.write(self.style.WARNING(
                        f"Created dummy audio file: {dummy_audio_full_path}. "
                        f"Replace this with a real (small) MP3 for better testing."
                    ))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Could not create dummy audio file at {dummy_audio_full_path}: {e}"))
                    self.stderr.write(self.style.ERROR("Please create it manually or ensure MEDIA_ROOT is writable."))
                    return


        languages = [lang_code for lang_code, lang_name in Level.LANGUAGE_CHOICES]
        num_levels_per_language = 10 // len(languages) # Distribute levels among languages
        extra_levels = 10 % len(languages)

        level_counter_overall = 1

        for lang_idx, lang_code in enumerate(languages):
            levels_for_this_lang = num_levels_per_language + (1 if lang_idx < extra_levels else 0)
            
            for i in range(1, levels_for_this_lang + 1):
                level_name = f"{lang_code.upper()} Practice Level {i}"
                
                # Check if level already exists to avoid duplicate unique `level` numbers
                if Level.objects.filter(level=level_counter_overall).exists():
                    self.stdout.write(self.style.WARNING(f"Level with number {level_counter_overall} already exists. Skipping."))
                    level_obj = Level.objects.get(level=level_counter_overall) # Get existing to add records
                else:
                    level_obj, created = Level.objects.get_or_create(
                        level=level_counter_overall, # Use overall counter for unique level numbers
                        defaults={
                            'name': level_name,
                            'language': lang_code,
                        }
                    )
                    if created:
                        self.stdout.write(f"Created Level: {level_obj}")
                    else:
                        # This case should ideally not happen if filter above works,
                        # but get_or_create is safe.
                        self.stdout.write(f"Found existing Level: {level_obj}")


                # Create 10 records for this level
                for j in range(10): # Creates records with order 0 through 9
                    record_text = f"This is sentence number {j + 1} for {level_obj.name}."
                    
                    # Check if record already exists for this level and order
                    if Record.objects.filter(level=level_obj, order=j).exists():
                        self.stdout.write(self.style.WARNING(f"Record order {j} for {level_obj} already exists. Skipping."))
                        continue

                    record = Record.objects.create(
                        level=level_obj,
                        # For FileField, assign the path relative to MEDIA_ROOT
                        pre_audio=DUMMY_AUDIO_FILE_PATH_RELATIVE,
                        text=record_text,
                        correct_audio=DUMMY_AUDIO_FILE_PATH_RELATIVE,
                        order=j  # Record order from 0 to 9
                    )
                    self.stdout.write(f"  Created Record: {record.text[:30]}... (Order: {record.order})")
                
                level_counter_overall += 1


        self.stdout.write(self.style.SUCCESS('Successfully populated levels and records.'))