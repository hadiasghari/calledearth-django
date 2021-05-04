from django.conf.urls import url
from django.urls import include, path
from . import views


urlpatterns = [
	# following are used by the mobile/website part of the game:
    #url(r'^$', views.web_home, name='earth_webhome'),
    # following are used by godot part of the game:
    url(r'^gonewgame$', views.godot_new_game),
    url(r'^gogettexts/(?P<game>\d+)/(?P<prompt>\d+)$', views.godot_get_texts),
    url(r'^gogetstats/(?P<game>\d+)$', views.godot_get_stats),
    url(r'^gosetprompt/(?P<game>\d+)/(?P<prompt>\d+)$', views.godot_set_prompt),
]
