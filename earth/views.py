from datetime import timedelta
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.http import Http404
from django.core.serializers import serialize
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .models import *


def web_home(request):
    # 1A. find an active game. if not, return sth like wait
    game = find_active_game()
    if not game:
        return render(request, 'earth.html', {'status': 'waitstart'})

    # 1B. if new session and no emoji selected, return emoji list
    if 'participant' not in request.session and 'e' not in request.GET:
        emojis = build_emoji_list()
            # TODO/options: (i) we could exclude already picked emojis (ii) ask for initials too
        return render(request, 'earth.html', {'status': 'pickemoji', 'emojis': emojis, 'gamek': game.pk})

    # 1C. if user has picked a new emoji (in URL), save participant in session, reload
    if 'e' in request.GET:
        em = request.GET['e']
        if Participant.objects.filter(game=game, emoji=em):
            # emoji exists!
            n = Participant.objects.filter(game=game, emoji=em).count()
            em += str(n+1)
        parti = Participant.objects.create(game=game, emoji=em)
        parti.geo = get_user_ip(request)  # TODO: store geolocation of participant!
        parti.save()
        request.session['participant'] = parti.pk  # cache for next time
        return HttpResponseRedirect(reverse('earth_webhome'))

    # 2. alright, load participant from session, before continuing...
    if 'participant' in request.session:
        try:
            parti = Participant.objects.get(pk=request.session['participant'], game=game)
        except:
            parti = None  # either participant doesn't exist or we are in a new game
            del request.session['participant']
            return HttpResponseRedirect(reverse('earth_webhome'))

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
        if game.last_save and game.last_save.lower().startswith('dance'):
            # Note/maybe make dancing own thing?
            return render(request, 'earth.html', {'status': 'dance', 'user': parti, 'gamek': game.pk})
        else:
            return render(request, 'earth.html', {'status': 'waitprompt', 'user': parti, 'gamek': game.pk})

    # 3B. otherwise send a prompt form (includes last thing user said)
    texts = Text.objects.filter(game=game, participant=parti).order_by('-pk')
    last = texts[0].text if texts else None
    # TODO: after the first prompt, the active prompt will change to a random suer entered one
    return render(request, 'earth.html', {'status': 'prompt', 'user': parti,
                                          'prompt': game.active_prompt,
                                          'gamek': game.pk, 'lastsaid': last,})


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
    return games[0] if games else None


def get_user_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def user_send_energy(request, partik):
    # this is an ajax call to send energy to godot
    # (note: participant also identifies the game)
    # TODO:  we could store these in a queue, or in the participant object for now
    parti = Participant.objects.get(pk=partik)
    event = EventQueue.objects.create(game=parti.game)
    event.event = "e_" + request.GET['energy'][0]  # one letter energy type
    event.info = "p_" + partik
    event.save()
    return JsonResponse(True, safe=False)


def user_needs_refresh(request, gamek):
    try:
        go = GamePlay.objects.get(pk=gamek)
    except GamePlay.DoesNotExist:
        raise Http404(f"No game {gamek}")
    if find_active_game() != gamek:
        return JsonResponse(True, safe=False)    # force a refresh if game changed!
    ep = request.GET['ep']  # expecting a prompt?
    ret = (ep=="1" and not go.active_prompt) or (ep=="0" and go.active_prompt)
    return JsonResponse(ret, safe=False)


def godot_new_game(request):
    game = GamePlay.objects.create()  # game defaults are good
    parti, cr = Participant.objects.get_or_create(pk=0, emoji="🎩")  # system user not tied to game;
    # delete all existing hello world messages from system!
    Text.objects.filter(participant=parti, prompt__isnull=True).delete()
    Text.objects.create(game=game, participant=parti, text="Hello World!")
    # let's also delete all empty participants & games, while at it, to clear admin UX
    Participant.objects.filter(text__isnull=True).delete()
    GamePlay.objects.filter(participant__isnull=True,
                            text__isnull=True,
                            eventqueue__isnull=True).delete()
    return JsonResponse(game.pk, safe=False)


def godot_get_texts(request, gamek, promptk):
    if promptk != "0":
        texts = Text.objects.filter(game=game, prompt__pk=promptk).order_by('pk')
        data = [{'pk': w.pk, 'text': w.text, 'parti_code': ord(w.participant.emoji)}
                for w in texts]
    else:
        texts = Text.objects.filter(game=game, prompt__isnull=True).order_by('pk')
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
    for p in Participant.objects.filter(game=go):
        emojies.append(ord(p.emoji))

    q_energy = ""
    q_after = 0 if 'qa' not in request.GET else int(request.GET['qa'])
    q_lastk = q_after
    for ev in EventQueue.objects.filter(game=go, pk__gt=q_after):  # not gte!
        if ev.event.startswith("e_"):
            q_energy += ev.event.replace("e_", "")
        q_lastk = ev.pk if ev.pk > q_lastk else q_lastk
    data = {'participants': emojies, 'q_energy': q_energy, 'q_lastk': q_lastk,
            'lastsave': go.last_save or "",}
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


def godot_save_game(request, gamek, loc):
    # reset activeprompt and save location
    go = GamePlay.objects.get(pk=gamek)
    go.active_prompt = None
    go.last_save = loc
    go.save()
    return JsonResponse(True, safe=False)
