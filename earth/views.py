from datetime import timedelta
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.http import Http404
from django.core.serializers import serialize
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .models import *


def web_home(request):
    # 1. find an active game. if not, return sth like wait
    game = find_active_game()
    if not game:
        return render(request, 'earth.html', {'status': 'waitstart'})

    # 2. if new session and no emoji selected, return emoji list
    if 'participant' not in request.session and 'e' not in request.GET:
        emojis = build_emoji_list()
        return render(request, 'earth.html', {'status': 'pickemoji', 'emojis': emojis})

    # 3. if user has picked a new emoji (in URL), save participant in session, reload
    if 'e' in request.GET:
        emoji = request.GET['e']
        parti = Participant.objects.create(game=game, emoji=emoji)
        # TODO: add geolocation of participant!
        request.session['participant'] = parti.pk  # cache for next time
        return HttpResponseRedirect(reverse('earth_webhome'))

    # 4. load participant from session
    if 'participant' in request.session:
        try:
            parti = Participant.objects.get(pk=request.session['participant'], game=game)
        except:
            parti = None  # either participant doesn't exist or we are in a new game
            del request.session['participant']
            return HttpResponseRedirect(reverse('earth_webhome'))

    # 5. did we get a form response, then save it and reload
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

    # for 6 & 7 load last thing participant said
    texts = Text.objects.filter(game=game, participant=parti).order_by('-pk')
    last = texts[0].text if texts else None

    # 6. no active-prompt?  wait for one in this stage of game-play
    if not game.active_prompt:
        if game.last_save and game.last_save.lower().startswith('dance'):
            # Note/maybe make dancing own thing?
            return render(request, 'earth.html', {'status': 'dance', 'emoji': parti.emoji,})
        else:
            return render(request, 'earth.html', {'status': 'waitprompt', 'emoji': parti.emoji,
                                              'lastsaid': last})
    # 7. otherwise send a prompt form
    return render(request, 'earth.html', {'status': 'prompt', 'emoji': parti.emoji,
                                          'prompt': game.active_prompt, 'lastsaid': last})


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


def godot_new_game(request):
    game = GamePlay.objects.create()  # game defaults are good
    parti, cr = Participant.objects.get_or_create(pk=0, emoji="🎩")  # system user not tied to game;
    # delete all existing hello world messages from system!
    Text.objects.filter(participant=parti, prompt__isnull=True).delete()
    Text.objects.create(game=game, participant=parti, text="Hello World!")
    # let's also delete all empty participants & games, while at it, to clear admin UX
    Participant.objects.filter(text__isnull=True).delete()
    GamePlay.objects.filter(participant__isnull=True, text__isnull=True).delete()
    return JsonResponse(game.pk, safe=False)


def godot_get_texts(request, game, prompt):
    if prompt != "0":
        texts = Text.objects.filter(game=game, prompt__pk=prompt).order_by('pk')
        data = [{'pk': w.pk, 'text': w.text, 'parti_code': ord(w.participant.emoji)}
                for w in texts]
    else:
        texts = Text.objects.filter(game=game, prompt__isnull=True).order_by('pk')
        data = [{'pk': w.pk, 'text': w.text, 'parti_code': ord(w.participant.emoji)}
                for w in texts]
    return JsonResponse(data, safe=False)


def godot_get_stats(request, game):
    # For HUD, return list of participants. maybe some other stuff too.
    try:
        go = GamePlay.objects.get(pk=game)  # isn't there a prettier way to do this?
    except GamePlay.DoesNotExist:
        raise Http404(f"No game {game}")
    partis = Participant.objects.filter(game=go)
    data = {'participants': [ord(p.emoji) for p in partis],
            'lastsave': go.last_save or ""}
    return JsonResponse(data)


def godot_set_prompt(request, game, prompt):
    # set activeprompt and return its text
    go = GamePlay.objects.get(pk=game)
    po, cr = Prompt.objects.get_or_create(pk=prompt)
    if cr:
        po.provocation = "!UNKNOWN PROMPT!"
        po.save()
    go.active_prompt = po
    go.save()
    return JsonResponse(po.provocation, safe=False)


def godot_save_game(request, game, loc):
    # reset activeprompt and save location
    go = GamePlay.objects.get(pk=game)
    go.active_prompt = None
    go.last_save = loc
    go.save()
    return JsonResponse(True, safe=False)
