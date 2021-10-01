from django.db import models
from django.utils import timezone


class GamePlay(models.Model):
	start_time = models.DateTimeField(default=timezone.now)  # (to get latest game)
	active = models.BooleanField(default=True)  # (can be unset in admin)
	game_ver = models.IntegerField(default=1)  # (for future game versions)
	godot_ip = models.CharField(max_length=50, null=True, blank=True)
	active_prompt = models.ForeignKey('Prompt', on_delete=models.SET_NULL, null=True, blank=True)
	state = models.CharField(max_length=10, blank=True, default="")
	description = models.TextField(blank=True, null=True)  # (for ourselves to recall this game)
	# Future: we could protect important GamePlays from being deleted by connecting them to a `protectedgames` table (with foreign key PROTECT)

	def __str__(self):
		return "GP{0}".format(self.pk)


class Participant(models.Model):
	game = models.ForeignKey(GamePlay, on_delete=models.CASCADE, null=True)  # can delete if has no Texts (PROTECT)
	joined_at = models.DateTimeField(default=timezone.now)
	emoji = models.CharField(max_length=10, default="👓")  # (similar to nickname, for game users)
	geo = models.CharField(max_length=50, blank=True, null=True)  # ip or geolocation

	def get_emoji1(self):
		return self.emoji[0] if len(self.emoji) >= 1 else "!"


class Prompt(models.Model):
	# we have some initial prompts. load fixture with: `manage.py loaddata`
	provocation = models.CharField(max_length=500)  # The Prompt Question
	active = models.BooleanField(default=True)
	comments = models.TextField(blank=True, null=True)
	char_limit = models.IntegerField(blank=True, null=True)  # defaults to 140 in UX
	# maybe in future: add a picture for the prompt
	# design note: location is 'view related' and hence set in godot (not in django/db)

	def __str__(self):
		return f"{self.pk}|{self.provocation[:10]}..."


class XGameLog(models.Model):
	# TODO 2021.05.20 -- delete this object and keep the log within godot
	game = models.ForeignKey(GamePlay, on_delete=models.CASCADE)  # can delete
	time = models.DateTimeField(default=timezone.now)
	event = models.CharField(max_length=50, default="", blank=True)
	info = models.TextField(blank=True, null=True)


class Text(models.Model):
	 game = models.ForeignKey(GamePlay, on_delete=models.PROTECT, null=True)
	 participant = models.ForeignKey(Participant, on_delete=models.PROTECT)
	 prompt = models.ForeignKey(Prompt, on_delete=models.PROTECT, null=True, blank=True)  # if response to prompt
	 prompt_inner = models.CharField(max_length=20, default="", blank=True)  # subprompt (to another user)
	 created_at = models.DateTimeField(default=timezone.now)
	 text = models.TextField()  # The text (words) enetered by the participant
	 flag = models.CharField(max_length=10, null=True, blank=True)

	 def __str__(self):
		 return f"{self.pk}|{self.text[:40]}..."
