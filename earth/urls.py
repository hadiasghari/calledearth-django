from django.conf.urls import url
from django.urls import include, path
from django.views.generic import RedirectView
from . import views


urlpatterns = [
    # following are used by the mobile/website part of the game:
    url(r'^$', RedirectView.as_view(pattern_name='earth_webhome2', permanent=False)),  # TODO: change this default for pre-vs-post performance mode
    #url(r'^$', RedirectView.as_view(pattern_name='earth_webstory', permanent=False)),  # TODO: change this default for pre-vs-post performance mode
    url(r'^story$', views.web_story, name='earth_webstory'),
    url(r'^play$', views.web_play, name='earth_webhome2'),
    url(r'^sendenergy/(?P<partik>\d+)$', views.user_send_energy, name='earth_sendenergy'),
    url(r'^needrefresh/(?P<gamek>\d+)$', views.user_needs_refresh, name='earth_needrefresh'),
    # following are used by godot part of the game:
    url(r'^gonewgame$', views.godot_new_game),
    url(r'^gogettexts/(?P<gamek>\d+)/(?P<promptk>\d+)$', views.godot_get_texts),
    url(r'^gogetstats/(?P<gamek>\d+)$', views.godot_get_stats),
    url(r'^gosetprompt/(?P<gamek>\d+)/(?P<promptk>\d+)$', views.godot_set_prompt),
    url(r'^gosetstate/(?P<gamek>\d+)/(?P<state>.+)$', views.godot_set_state),
    #url(r'^golog/(?P<gamek>\d+)/(?P<event>.+)$', views.godot_log_event),
]
