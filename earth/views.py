from datetime import timedelta
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.http import Http404
from django.core.serializers import serialize
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from .models import *

## HA 20221119 WS4REDIS was a hacky solution to have websockets and improve the django/heroku responsivity/scability
#              but it broke after some Heroku Redis update (gives AWS REDIS peer reset connection error).
#              So removing it for now as test. 
#              And in general, I think a better solution for WCIE is to remove Heroku/Django all together (given all live performance issues)
from ws4redis.redis_store import RedisMessage
from ws4redis.publisher import RedisPublisher


def push_message_clients(msg='reload'):
    redmsg = RedisMessage(msg)
    RedisPublisher(facility='webusers', broadcast=True).publish_message(redmsg)
    #pass


def web_story(request):
    # post performance results of one game.
    # the homepage is redirected here manually via urls.py
    # TODO: this should be a state activated in DB/CACHE OR SETTINGS with the game_id marked too...
    the_game = 1467  # Ams20211001: 1467 # ARTEZ20210520: 1373
    try:
        go = GamePlay.objects.get(pk=the_game)
    except GamePlay.DoesNotExist:
        raise Http404(f"Game {the_game} not found")
    texts = Text.objects.filter(game__pk=the_game).order_by('prompt', 'pk')
    return render(request, 'earth_story.html', {'game': go, 'texts': texts})


def web_play(request):
    # 1. find an active game
    game = find_active_game()
    if not game:
        # note, we could add a special get-param to show last game story when no new game
        return render(request, 'earth_waitstart.html', {})

    # 2. get participant from session (or emoji form)
    parti, response = get_participant_or_httpresponse(game, request)
    if not parti:
        return response if response else HttpResponseRedirect(reverse('earth_webhome2'))

    # 3. did we get a form response, then save it and reload so not to lose data
    if 'f_text' in request.GET:
        f_t = request.GET['f_text']  #.replace("\n", "")  # remove new lines
        f_p = Prompt.objects.get(pk=request.GET['f_pk'])
        if f_t:
            texts_tosave = maybe_expand_ftext(f_t)
            for t in texts_tosave:
                # maybe cheats should be set with the system user?
                text = Text.objects.create(game=game, participant=parti, prompt=f_p, text=t)
                text.save()
            # continue in this state until active_prompt is reset by GODOT engine
            return HttpResponseRedirect(reverse('earth_webhome2'))

    # 4A. handle a variety of game states
    if game.state == "credits":
        # credits+story template - shows whole game story as narrated by audence...
        texts = Text.objects.filter(game=game).order_by('prompt', 'pk')
        return render(request, 'earth_story.html', {'texts': texts})

    # 4B. not in credits and no active-prompt: cheering mode.
    if not game.active_prompt:
        # this is a number of screen including waiting for prompt, revival, and dancing.
        # only difference among them is the sentence shown which template can choose
        # (202109: testing WS4Redis callbacks to reduce refresh in cheer-page)
        push_message_clients('welcome [' + parti.get_emoji1() + ']')
        return render(request, 'earth_cheer.html', {'state': game.state, 'participant': parti, 'gamek': game.pk})

    # 4C. so we are in writing mode. show a prompt form (includes last thing user said)
    # (Future: after the first prompt, the active prompt will change to a random user entered one)
    texts = Text.objects.filter(game=game, participant=parti).order_by('-pk')
    last = texts[0].text if texts else None
    push_message_clients('welcome [' + parti.get_emoji1() + ']')
    return render(request, 'earth_write.html', {'emoji': parti.get_emoji1(),
                                                'lastsaid': last,
                                                'prompt': game.active_prompt,
                                                'gamek': game.pk,})


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
        return None, None

    # otherwise, load participant from session, and return that... (reload if fail)
    assert 'participant' in request.session
    try:
        parti = Participant.objects.get(pk=request.session['participant'], game=game)
        return parti, None
    except:
        parti = None  # either participant doesn't exist or we are in a new game
        del request.session['participant']
        return None, None


def maybe_expand_ftext(ftext):
    # if there is a hidden command in the entered text prompt, expand it with test data....
    if not ftext.startswith("!@#") and not ftext.startswith("qwe"):
        return [ftext]
    try:
        n = int(ftext.replace("!@#", "").replace("qwe", ""))
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
        lt.append(t[:116] + "___!")  # add max 120 chars
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
    last_hour = timezone.now() - timedelta(hours=2)
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
    # This is an ajax call to send energy to godot;
    # (we store it in a CACHE queue and only commit to DB in getstats for speed)

    # TODO: 202109 THIS COULD BE replaced with websockets (pushed from browser).. needs sth other than WS4REDIS
    ecache = cache.get(f"e_{partik}") or ""
    ecache += request.GET['energy'][0]  # one letter energy type
    cache.set(f"e_{partik}", ecache)
    return JsonResponse(True, safe=False)


def user_needs_refresh(request, gamek):
    # force a refresh if active game has changed, or if gamestate has changed
    try:
        go = GamePlay.objects.get(pk=gamek)
    except GamePlay.DoesNotExist:
        return JsonResponse(True, safe=False)
    if find_active_game() != go:
        return JsonResponse(True, safe=False)

    last_state = request.GET['st']
    refresh = (last_state != str(go.state))
    #print("DBG:", last_state, 'vs.', go.state, "=>", refresh)
    return JsonResponse(refresh, safe=False)


def godot_new_game(request):
    # Let's delete all empty participants, games, gamelogs (via cascade),to clear admin UX
    # (When we started testing we used a system user not tied to any prompt; not anymore)
    last_hour = timezone.now() - timedelta(hours=1)
    try:
        Participant.objects.filter(text__isnull=True, joined_at__lt=last_hour).delete()
    except:
        pass
    try:
        GamePlay.objects.filter(text__isnull=True, start_time__lt=last_hour).delete()
    except:
        pass
    game = GamePlay.objects.create()  # most game defaults are good
    game.godot_ip = get_client_ip(request)  # in case we ever want to do direct websockets
    game.save()
    # Note: log move to Godot, was: GameLog.objects.create(game=game, event="new_game")

    # (202109) send reload to webclients (in cheer page; since gameid will change)
    push_message_clients()

    return JsonResponse(game.pk, safe=False)


def godot_get_texts(request, gamek, promptk):
    texts = Text.objects.filter(game__pk=gamek, prompt__pk=promptk).order_by('pk')
    data = [{'pk': w.pk, 'text': w.text,
             'parti_code': ord(w.participant.emoji[0]) if len(w.participant.emoji) >= 1 else "?",
             'parti_code2': w.participant.emoji[1] if len(w.participant.emoji) > 1 else ""}
            for w in texts]
    #print(f"DEBUG godot_get_texts(req, {gamek}, {promptk}) → {data}")
    return JsonResponse(data, safe=False)


def godot_get_stats(request, gamek):
    # For HUD, return list of participants. some other stuff too.
    try:
        go = GamePlay.objects.get(pk=gamek)  # isn't there a prettier way to do this?
    except GamePlay.DoesNotExist:
        raise Http404(f"No game {gamek}")

    emojies = []
    emojies_plus = []
    energies = ""
    for p in Participant.objects.filter(game=go):
        emojies.append(ord(p.emoji[0]))
        emojies_plus.append(p.emoji)  # includes the full emoji in case we want to display it
        # check all queued energ (powerups)

        # TODO: 202109 THIS PART SHOULD BE REPLACED WITH READING FROM WS4REDIS QUEUE DIRETLY
        # not so interesting in the current library...
        energy = cache.get(f"e_{p.pk}")
        if energy:
            energies += energy
            cache.set(f"e_{p.pk}", "")

    # Note: log removed, was: if energies: GameLog.objects.create(game=go, event=f"energy", info=energies)
    data = {'participants': emojies, 'participants+': emojies_plus, 'q_energy': energies,  }
    return JsonResponse(data)


def godot_set_prompt(request, gamek, promptk):
    # set activeprompt and return its text
    go = GamePlay.objects.get(pk=gamek)
    if promptk == "0" or promptk == 0:
        po = None
        go.active_prompt = None
        go.state = "?"  # (decide if this is correct)
        go.save()
        # Note: log move to Godot, was: GameLog.objects.create(game=go, event=f"prompt_unset", info=None)  # log it too
    else:
        po, cr = Prompt.objects.get_or_create(pk=promptk)
        if cr:
            po.provocation = "!UNKNOWN PROMPT!"
            po.save()
        go.active_prompt = po
        go.state = "writing"
        go.save()
        # Note: log move to Godot, was: GameLog.objects.create(game=go, event=f"prompt_{promptk}", info=None)  # log it too

    push_message_clients()  # 202109 send reload to webclients
    return JsonResponse(po.provocation if po else "", safe=False)


def godot_set_state(request, gamek, state):
    # game state has changed, record it for web UX (and in DB)....
    go = GamePlay.objects.get(pk=gamek)
    extra_info = request.GET['info'] if 'info' in request.GET else None
    if state not in ("milestone", "event"):
        # milestones/events used to logged (so no game stage change; now we ignore them fully!)
        # logs move to Godot, had: GameLog.objects.create(game=go, event="state_" + state, info=extra_info)
        #                      or: GameLog.objects.create(game=go, event="milestone", info=extra_info)
        go.state = state
        go.save()
        push_message_clients()  # 202109 send reload to webclients, I THINK! :)
        
    if state != "writing":
        go.active_prompt = None  # also let's unset the prompt
        go.save()
    return JsonResponse(True, safe=False)
