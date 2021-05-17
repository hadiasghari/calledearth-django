from datetime import timedelta
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.http import Http404
from django.core.serializers import serialize
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from .models import *


def web_home(request):
    # 1. find an active game
    game = find_active_game()
    if not game:
        return render(request, 'earth_waitstart.html', {})

    # 2. get participant from session (or emoji form)
    parti, response = get_participant_or_httpresponse(game, request)
    if not parti:
        return response


    # TODO game 'states'
    # - wait-start
    # - write (active-rpompt/writing/camera)
    # - search (we just wait) + revive + dance + continue:  in all we can send energy
    # - credits (finished, show all messages)

    # 3A. did we get a form response, then save it and reload
    if 'f_text' in request.GET:
        f_t = request.GET['f_text']
        f_p = Prompt.objects.get(pk=request.GET['f_pk'])
        if f_t:
            texts_tosave = maybe_expand_ftext(f_t)
            for t in texts_tosave:
                # maybe cheats should be set with the system user?
                text = Text.objects.create(game=game, participant=parti, prompt=f_p, text=t)
                text.save()
            # continue in this state until active_prompt is reset by GODOT engine
            return HttpResponseRedirect(reverse('earth_webhome'))

    # 4. no active-prompt?  wait for one in this stage of game-play
    # Q: I wonder if part of this logic cna be moved to template since they all return similar thigns
    # TODO: give dance, etc, and yet to add credit screen, maybe this needs a nicer flowchart :)
    # TODO: REVIVAL SCREEN ALSO
    if not game.active_prompt:
        #if game.last_save and game.last_save.lower().startswith('dance'):
        dancing = False  # TODO get this from GameLog
        return render(request, 'earth_cheer.html', {'dance': dancing, 'participant': parti, 'gamek': game.pk})

    # 3B. otherwise send a prompt form (includes last thing user said)
    texts = Text.objects.filter(game=game, participant=parti).order_by('-pk')
    last = texts[0].text if texts else None
    # TODO: after the first prompt, the active prompt will change to a random suer entered one
    return render(request, 'earth_write.html', {'emoji': parti.emoji, 'lastsaid': last,
                                                 'prompt': game.active_prompt, 'gamek': game.pk,})


def get_participant_or_httpresponse(game, request):
    # if no participant saved or just picked, then return emoji list
    if 'participant' not in request.session and 'e' not in request.GET:
        return None, render(request, 'earth_pickemoji.html', {'emojis': build_emoji_list()})

    # has user picked a (new) emoji? if so lets create a participant for session and reload
    if 'e' in request.GET:
        e = request.GET['e']
        if Participant.objects.filter(game=game, emoji=e):
            # emoji exists, add suffix
            n = Participant.objects.filter(game=game, emoji=e).count()
            e += str(n+1)
        parti = Participant.objects.create(game=game, emoji=e)
        parti.geo = get_client_ip(request)
        if '.' in parti.geo:
            # pseudonymize the client IP address for privacy (needs fix for IPv6)
            parti.geo = ".".join(parti.geo.split('.')[:2]) + ".0.0"
        parti.save()
        request.session['participant'] = parti.pk  # cache for next time
        return None, HttpResponseRedirect(reverse('earth_webhome'))

    # otherwise, load participant from session, and return that... (reload if fail)
    assert 'participant' in request.session
    try:
        parti = Participant.objects.get(pk=request.session['participant'], game=game)
        return parti, None
    except:
        parti = None  # either participant doesn't exist or we are in a new game
        del request.session['participant']
        return None, HttpResponseRedirect(reverse('earth_webhome'))


def maybe_expand_ftext(ftext):
    # if there is a hidden command in the entered text prompt, expand it with test data....
    if not ftext.startswith("!@#") and not ftext.startswith("QWE"):
        return [ftext]
    try:
        n = int(ftext.replace("!@#", "").replace("QWE", ""))
    except:
        return [ftext]

    # return test data!
    test_strings = ["There were many words for her.",
	      "Zoinks",		"Crikey", "None of them were more than sound.",
	      "By coincidence, or by choice, or by miraculous design, " \
	            + "she settled into such a particular orbit around the sun that after the moon had been knocked from her belly " \
	                  + "and pulled the water into sapphire blue oceans " \
	                        + "the fire and brimstone had simmered, and the land had stopped buckling and heaving with such relentless vigor, " \
	                              + "she whispered a secret code amongst the atoms, and life was born.",
	      "She rocked her new creation and spun and danced around the bright sun as her children multiplied in number, wisdom, and beauty." ,
          "Oh my God",		"WTF",
	       "The End!"]
    lt = []
    for i in range(n):
        t = test_strings[i%len(test_strings)]
        lt.append(t[:140])  # add max 140 chars
    return lt


def build_emoji_list():
    emojis = []
    # see https://www.w3schools.com/charsets/ref_emoji.asp
    # note, not every character exists, also on the GODOT side, so these ranges need to be tested
    # (also could offset with a random 1-5 to add variety but don't re missing ones)
    for i in range(128640, 128700, 5):
        emojis.append(chr(i))
    for i in range(129296, 129390, 5):
        emojis.append(chr(i))
    for i in range(129411, 129436, 5):
        emojis.append(chr(i))
    for i in range(129491, 129510, 5):
        emojis.append(chr(i))
    return emojis


def find_active_game():
    last_hour = timezone.now() - timedelta(hours=1)
    games = GamePlay.objects.filter(active=1, game_ver=1, start_time__gt=last_hour).order_by('-pk')
    # can be memcached if necessary
    return games[0] if games else None


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def user_send_energy(request, partik):
    # this is an ajax call to send energy to godot
    # we store it in a memache queue and only commit to DB in getstats for speed
    ecache = cache.get(f"e_{partik}") or ""
    ecache += request.GET['energy'][0]  # one letter energy type
    cache.set(f"e_{partik}", ecache)
    return JsonResponse(True, safe=False)


def user_needs_refresh(request, gamek):
    try:
        go = GamePlay.objects.get(pk=gamek)
    except GamePlay.DoesNotExist:
        raise Http404(f"No game {gamek}")
    if find_active_game() != go:
        return JsonResponse(True, safe=False)    # force a refresh if game changed!

    expecting_prompt = int(request.GET['ep'])
    is_active_prompt = (go.active_prompt is not None) * 1
    refresh = (expecting_prompt != is_active_prompt)
    return JsonResponse(refresh, safe=False)


def godot_new_game(request):
    game = GamePlay.objects.create()  # most game defaults are good
    game.godot_ip = get_client_ip(request)  # in case we ever want to do direct websockets
    game.save()
    parti, cr = Participant.objects.get_or_create(pk=0, emoji="🎩")  # system user not tied to game;
    # delete all existing system (hello world) messages from system!
    Text.objects.filter(participant=parti, prompt__isnull=True).delete()
    Text.objects.create(game=game, participant=parti, text="Hello World!")
    # let's also delete all empty participants & games, while at it, to clear admin UX
    Participant.objects.filter(text__isnull=True).delete()
    # we should probably delete all system stuff
    GamePlay.objects.filter(text__isnull=True).delete()
    # was: participant__isnull=True, gamelog__isnull=True).delete()
    return JsonResponse(game.pk, safe=False)


def godot_get_texts(request, gamek, promptk):
    if promptk != "0":
        texts = Text.objects.filter(game__pk=gamek, prompt__pk=promptk).order_by('pk')
        data = [{'pk': w.pk, 'text': w.text, 'parti_code': ord(w.participant.emoji)}
                for w in texts]
    else:
        texts = Text.objects.filter(game__pk=gamek, prompt__isnull=True).order_by('pk')
        data = [{'pk': w.pk, 'text': w.text, 'parti_code': ord(w.participant.emoji)}
                for w in texts]
    return JsonResponse(data, safe=False)


def godot_get_stats(request, gamek):
    # For HUD, return list of participants. some other stuff too.
    try:
        go = GamePlay.objects.get(pk=gamek)  # isn't there a prettier way to do this?
    except GamePlay.DoesNotExist:
        raise Http404(f"No game {gamek}")

    emojies = []
    energies = ""
    for p in Participant.objects.filter(game=go):
        emojies.append(ord(p.emoji))
        # check all queued energ (powerups)
        energy = cache.get(f"e_{p.pk}")
        if energy:
            log = GameLog.objects.create(game=go, event=f"energy_{p.pk}", info=energy)
            energies += energy
            cache.set(f"e_{p.pk}", "")

    data = {'participants': emojies,
            'q_energy': energies,  # lets rename on server
            'q_lastk': 0,  # TODO: unnecessay (remove upon changing godot code)
            'lastsave': "",}  # TODO: LAST SAVE IF NECESSARY (PERHAPS NOT)
    return JsonResponse(data)


def godot_set_prompt(request, gamek, promptk):
    # set activeprompt and return its text
    go = GamePlay.objects.get(pk=gamek)
    po, cr = Prompt.objects.get_or_create(pk=promptk)
    if cr:
        po.provocation = "!UNKNOWN PROMPT!"
        po.save()
    go.active_prompt = po
    go.save()
    return JsonResponse(po.provocation, safe=False)


def godot_set_state(request, gamek, state):
    # game state has changed, record it for web users....
    go = GamePlay.objects.get(pk=gamek)
    go.state = state
    if state.lower() != "writing":
        go.active_prompt = None
    go.save()
    # also let's create a log for this change
    GameLog.objects.create(game=go, event="st_" + state)
    return JsonResponse(True, safe=False)


def godot_log_event(request, gamek, event):
    # this method is used to log major game events as they happen (incl death etc)
    info = None
    if 'info' in request.GET:
        info = request.GET['info']
    GameLog.objects.create(game=go, event=event, info=info)
    return JsonResponse(True, safe=False)
