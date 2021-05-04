from django.contrib import admin
from .models import *
from django.utils import timezone
from datetime import timedelta


class TextAdmin(admin.ModelAdmin):
    list_display = ['pk', 'game', 'who', 'created_at', 'prompt', 'text']
    list_filter = ['game']
    ordering = ['-pk', ]

    def who(self, obj):
        return obj.participant.emoji if obj and obj.participant else ""

    def prompt(self, obj):
        return obj.prompt if obj else ""



class GamePlayAdmin(admin.ModelAdmin):
    list_display = ['pk', 'start_time', 'is_active', 'active_prompt', 'texts', 'participants']
    ordering = ['-pk', ]

    def is_active(self, obj):
        last_hour = timezone.now() - timedelta(hours=1)
        b = obj.active and obj.start_time > last_hour
        return b
    is_active.boolean = True

    def texts(self, obj):
        return obj.text_set.count()

    def participants(self, obj):
        return obj.participant_set.count()


class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['pk', 'game', 'emoji', 'joined_at', 'geo', 'texts']
    list_filter = ['game']
    ordering = ['-pk', ]

    def texts(self, obj):
        return obj.text_set.count()


class PromptAdmin(admin.ModelAdmin):
    list_display = ['pk', 'level', 'provocation', 'active', 'responses']
    ordering = ['-pk', ]

    def responses(self, obj):
        return obj.text_set.count()



admin.site.register(GamePlay, GamePlayAdmin)
admin.site.register(Participant, ParticipantAdmin)
admin.site.register(Text, TextAdmin)
admin.site.register(Prompt, PromptAdmin)
