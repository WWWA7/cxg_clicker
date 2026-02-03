from django.db import models
from django.contrib.auth.models import User

class Building(models.Model):
    key = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    flavor = models.CharField(max_length=200)
    base_price = models.BigIntegerField()
    price_growth = models.FloatField(default=1.15)
    base_per_second = models.FloatField(default=0.0)
    base_per_click = models.FloatField(default=0.0)

    def __str__(self):
        return self.name

class GameState(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    apples = models.BigIntegerField(default=0)
    apples_total = models.BigIntegerField(default=0)
    clicks = models.BigIntegerField(default=0)
    upgrade_level = models.IntegerField(default=0)
    last_tick = models.DateTimeField(auto_now_add=True)

    buff_multiplier = models.FloatField(default=1.0)
    buff_ends_at = models.DateTimeField(null=True, blank=True)

    event_id = models.IntegerField(null=True, blank=True)
    event_multiplier = models.FloatField(default=1.0)
    event_expires_at = models.DateTimeField(null=True, blank=True)
    last_event_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}"

class UserBuilding(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0)

    class Meta:
        unique_together = ("user", "building")

class Achievement(models.Model):
    key = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    rule = models.CharField(max_length=200)
    kind = models.CharField(max_length=30)
    threshold = models.BigIntegerField()
    building_key = models.CharField(max_length=50, blank=True, default="")
    reward_apples = models.BigIntegerField(default=0)
    reward_multiplier = models.FloatField(default=1.0)
    reward_seconds = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "achievement")

class UpgradeCard(models.Model):
    key = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    cost = models.BigIntegerField(default=0)
    multiplier = models.FloatField(default=1.5)
    target_key = models.CharField(max_length=50)  # 对应 Building.key

    def __str__(self):
        return self.name

class UserUpgradeCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card = models.ForeignKey(UpgradeCard, on_delete=models.CASCADE)
    owned = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "card")
