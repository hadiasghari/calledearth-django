from django.db import models
from django.utils import timezone


class GamePlay(models.Model):
	start_time = models.DateTimeField(default=timezone.now)  # (to get latest game)
	active = models.BooleanField(default=True)  # (can be unset in admin)
	game_ver = models.IntegerField(default=1)  # (for future game versions)
	godot_ip = models.CharField(max_length=50, null=True, blank=True)
	active_prompt = models.ForeignKey('Prompt', on_delete=models.SET_NULL, null=True, blank=True)
	#last_save = models.CharField()  # understood by godot >> use GameLog instead!
	description = models.TextField(blank=True, null=True)  # (for ourselves to recall this game)

	def __str__(self):
		return "GP{0}".format(self.pk)


class Participant(models.Model):
	game = models.ForeignKey(GamePlay, on_delete=models.PROTECT, null=True)
	joined_at = models.DateTimeField(default=timezone.now)
	emoji = models.CharField(max_length=10, default="👓")  # (similar to nickname, for game users)
	geo = models.CharField(max_length=50, blank=True, null=True)  # ip or geolocation


class Prompt(models.Model):
	# we have some initial prompts. load fixture with: `manage.py loaddata`
	provocation = models.CharField(max_length=500)  # The Prompt Question
	active = models.BooleanField(default=True)
	description = models.TextField(blank=True, null=True)
	# maybe in future: add a picture for the prompt
	# location & fill correctly are view related and set in godot (not in django/db)

	def __str__(self):
		return f"{self.pk} ({self.provocation[:10]}...)"


class GameLog(models.Model):
	game = models.ForeignKey(GamePlay, on_delete=models.PROTECT)
	time = models.DateTimeField(default=timezone.now)
	event = models.CharField(max_length=20, default="", blank=True)
	info = models.CharField(max_length=200, blank=True, null=True) # e.g. participant


class Text(models.Model):
	 game = models.ForeignKey(GamePlay, on_delete=models.PROTECT, null=True)
	 participant = models.ForeignKey(Participant, on_delete=models.PROTECT)
	 prompt = models.ForeignKey(Prompt, on_delete=models.PROTECT, null=True, blank=True)  # if response to prompt
	 prompt_inner = models.CharField(max_length=20, default="", blank=True)  # subprompt (to another user)
	 created_at = models.DateTimeField(default=timezone.now)
	 text = models.TextField()  # The text (words) enetered by the participant
