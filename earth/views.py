from datetime import timedelta
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
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
            text = Text.objects.create(game=game, participant=parti, prompt=f_p, text=f_t)
            text.save()
            game.active_prompt = None
            game.save()
            return HttpResponseRedirect(reverse('earth_webhome'))  # is this correct? no form?

    # 6. no active-prompt?  wait for one in this stage of game-play
    if not game.active_prompt:
        texts = Text.objects.filter(game=game, participant=parti).order_by('-pk')
        last = texts[0].text if texts else None
        return render(request, 'earth.html', {'status': 'waitprompt', 'emoji': parti.emoji,
                                              'lastsaid': last})
    # 7. otherwise send a prompt form
    return render(request, 'earth.html', {'status': 'prompt', 'emoji': parti.emoji,
                                          'prompt': game.active_prompt})


def build_emoji_list():
    emojis = []
    # see https://www.w3schools.com/charsets/ref_emoji.asp
    for i in range(128640, 128700, 5):
        emojis.append(chr(i))  # could offset with a random 1-5 to add variety
    for i in range(129296, 129510, 5):
        emojis.append(chr(i))
    emojis.remove('\U0001f979')  # remove non-existsant emoji
    emojis.remove('\U0001f9ab')
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
    # TODO: perhaps add: request.GET["afterpk"]   # to get only latest texts
    # TODO: perhaps add the prompt as pk0
    if prompt == "99999":
        # test data!
        data = [{ 'pk': i, 'text': f'message {i}', 'parti_code': 10067} for i in range(15)]
    elif prompt != "0":
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
    partis = Participant.objects.filter(game=game)
    data = {'participants': [ord(p.emoji) for p in partis]}
    return JsonResponse(data)


#for POST: @csrf_exempt
def godot_set_prompt(request, game, prompt):
    go = GamePlay.objects.get(pk=game)
    po = Prompt.objects.get(pk=prompt)  # request.POST['prompt'])
    go.active_prompt = po
    # LATER: go.last_location = request.POST['location']
    go.save()
    return JsonResponse(True, safe=False)
