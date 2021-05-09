from django.db import models
from django.utils import timezone


class GamePlay(models.Model):
	start_time = models.DateTimeField(default=timezone.now)  # (to get latest game)
	active = models.BooleanField(default=True)  # set to False when quitting if we can
	game_ver = models.IntegerField(default=1)  # for future game versions
	active_prompt = models.ForeignKey('Prompt', on_delete=models.SET_NULL, null=True, blank=True)
	last_location = models.CharField(max_length=50, null=True, blank=True)  # location of active prompt/avatar
	# might also need last avatar level as the game proceeds
	description = models.TextField(blank=True, null=True)  # for ourselves to recall this game

	def __str__(self):
		return "GP{0}".format(self.pk)


class Participant(models.Model):
	game = models.ForeignKey(GamePlay, on_delete=models.PROTECT, null=True)
	joined_at = models.DateTimeField(default=timezone.now)
	emoji = models.CharField(max_length=10, default="👓")  # similar to nickname, for game users
	typing = models.NullBooleanField()   # for future to show is typing on screen
	geo = models.CharField(max_length=50, blank=True, null=True)  # geolocation


class Prompt(models.Model):
	# we have some initial prompts. load fixture with: `manage.py loaddata`
	provocation = models.CharField(max_length=500)  # The Prompt Question
	# maybe in future: add a picture for the prompt
	active = models.BooleanField(default=True)
	#level = models.CharField(max_length=10, null=True, blank=True)
	description = models.TextField(blank=True, null=True)
	# location & fill correctly are view related and should be in godot not in django/db

	def __str__(self):
		return f"[{self.level}.{self.pk}] {self.provocation[:30]}"


class Text(models.Model):
	 game = models.ForeignKey(GamePlay, on_delete=models.PROTECT, null=True)
	 participant = models.ForeignKey(Participant, on_delete=models.PROTECT)
	 prompt = models.ForeignKey(Prompt, on_delete=models.PROTECT, null=True, blank=True)  # if response to prompt
	 created_at = models.DateTimeField(default=timezone.now)
	 #level = models.IntegerField(default=1)  # for when more levels
	 #location = models.FloatField(null=True, blank=True)  # where the words have been entered
	 text = models.TextField()  # The text (words) enetered by the participant
	 color = models.IntegerField(blank=True, null=True)
