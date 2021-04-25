from django.contrib import admin
from .models import *
from django.utils import timezone
from datetime import timedelta


class TextAdmin(admin.ModelAdmin):
    list_display = ['pk', 'game', 'who', 'created_at', 'location', 'text']
    list_filter = ['game']
    ordering = ['-pk', ]

    def who(self, obj):
        try:
            s = obj.participant.emoji
        except:
            s = ""
        return s



class GamePlayAdmin(admin.ModelAdmin):
    list_display = ['pk', 'start_time', 'is_active', 'notes']
    ordering = ['-pk', ]

    def is_active(self, obj):
        last_hour = timezone.now() - timedelta(hours=1)
        b = obj.active and obj.start_time > last_hour
        return b
    is_active.boolean = True


class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['pk', 'game', 'joined_at', 'emoji']
    list_filter = ['game']
    ordering = ['-pk', ]


admin.site.register(GamePlay, GamePlayAdmin)
admin.site.register(Participant, ParticipantAdmin)
admin.site.register(Text, TextAdmin)
admin.site.register(Prompt)
