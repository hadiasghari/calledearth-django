# -*- coding: utf-8 -*-
from django import VERSION as DJANGO_VERSION
if DJANGO_VERSION < (1, 10):
    from django.conf.urls import url, patterns, include
    from django.core.urlresolvers import reverse_lazy
elif DJANGO_VERSION < (2, 0):
    from django.conf.urls import url, include
    from django.urls import reverse_lazy
else:
    from django.urls import path, include
    from django.urls import reverse_lazy
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import RedirectView
#from django.contrib import admin
from .views import BroadcastChatView, UserChatView, GroupChatView
#admin.autodiscover()


urlpatterns = [
        path('chat/', BroadcastChatView.as_view(), name='broadcast_chat'),
        path('userchat/', UserChatView.as_view(), name='user_chat'),
        path('groupchat/', GroupChatView.as_view(), name='group_chat'),
        path('accounts/', include('django.contrib.auth.urls')),
        path('', RedirectView.as_view(url=reverse_lazy('broadcast_chat'))),
    ]
