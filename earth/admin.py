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


def deactivate_game(modeladmin, request, queryset):
    queryset.update(active=False)
deactivate_game.short_description='Deactivate selected games'

class GamePlayAdmin(admin.ModelAdmin):
    list_display = ['pk', 'start_time', 'is_active', 'active_prompt', 'texts', 'participants']
    ordering = ['-pk', ]
    actions = [deactivate_game]

    def is_active(self, obj):
        last_hour = timezone.now() - timedelta(hours=1)
        b = obj.active and obj.start_time > last_hour
        return b
    is_active.boolean = True

    # TODO: last_save can come from GameLog if desired

    def texts(self, obj):
        return obj.text_set.count()

    def participants(self, obj):
        return obj.participant_set.count()


class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['pk', 'game', 'emoji', 'energy', 'texts', 'joined_min']
    list_filter = ['game']
    ordering = ['-pk', ]

    def texts(self, obj):
        return obj.text_set.count()

    def joined_min(self, obj):
        try:
            return (obj.joined_at - obj.game.start_time).seconds // 60
        except:
            return ""

    def energy(self, obj):
        return ""   # TODO: return from GameLog if saved...!


class PromptAdmin(admin.ModelAdmin):
    list_display = ['pk', 'provocation', 'active', 'responses']
    ordering = ['-pk', ]

    def responses(self, obj):
        return obj.text_set.count()


class GameLogAdmin(admin.ModelAdmin):
   list_display = ['pk', 'game', 'time', 'event', 'info']
   ordering = ['-pk', ]


admin.site.register(GamePlay, GamePlayAdmin)
admin.site.register(Prompt, PromptAdmin)
admin.site.register(Participant, ParticipantAdmin)
admin.site.register(Text, TextAdmin)
admin.site.register(GameLog, GameLogAdmin)
