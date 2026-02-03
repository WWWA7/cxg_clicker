from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Building(models.Model):
    key = models.CharField("键名", max_length=50, unique=True)
    name = models.CharField("名称", max_length=100)
    flavor = models.CharField("描述", max_length=200)
    base_price = models.BigIntegerField("基础价格")
    price_growth = models.FloatField("价格增长倍率", default=1.15)
    base_per_second = models.FloatField("每秒产出", default=0.0)
    base_per_click = models.FloatField("每点击产出", default=0.0)

    class Meta:
        verbose_name = "建筑"
        verbose_name_plural = "建筑"

    def __str__(self):
        return self.name


class GameState(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="用户")
    apples = models.BigIntegerField("当前点数", default=0)
    apples_total = models.BigIntegerField("累计点数", default=0)
    clicks = models.BigIntegerField("点击次数", default=0)
    upgrade_level = models.IntegerField("成长等级", default=0)
    last_tick = models.DateTimeField("上次结算时间", default=timezone.now)

    buff_multiplier = models.FloatField("加成倍率", default=1.0)
    buff_ends_at = models.DateTimeField("加成结束时间", null=True, blank=True)

    event_id = models.IntegerField("事件ID", null=True, blank=True)
    event_multiplier = models.FloatField("事件倍率", default=1.0)
    event_expires_at = models.DateTimeField("事件过期时间", null=True, blank=True)
    last_event_at = models.DateTimeField("上次事件时间", null=True, blank=True)

    class Meta:
        verbose_name = "玩家状态"
        verbose_name_plural = "玩家状态"

    def __str__(self):
        return f"{self.user.username}"


class UserBuilding(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    building = models.ForeignKey(Building, on_delete=models.CASCADE, verbose_name="建筑")
    amount = models.IntegerField("拥有数量", default=0)

    class Meta:
        unique_together = ("user", "building")
        verbose_name = "用户建筑"
        verbose_name_plural = "用户建筑"


class Achievement(models.Model):
    key = models.CharField("键名", max_length=50, unique=True)
    name = models.CharField("名称", max_length=100)
    rule = models.CharField("规则描述", max_length=200)
    kind = models.CharField("类型", max_length=30)
    threshold = models.BigIntegerField("达成阈值")
    building_key = models.CharField("目标建筑键", max_length=50, blank=True, default="")
    reward_apples = models.BigIntegerField("奖励点数", default=0)
    reward_multiplier = models.FloatField("奖励倍率", default=1.0)
    reward_seconds = models.IntegerField("奖励时长(秒)", default=0)

    class Meta:
        verbose_name = "成就"
        verbose_name_plural = "成就"

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, verbose_name="成就")
    unlocked = models.BooleanField("是否解锁", default=False)

    class Meta:
        unique_together = ("user", "achievement")
        verbose_name = "用户成就"
        verbose_name_plural = "用户成就"


class UpgradeCard(models.Model):
    key = models.CharField("键名", max_length=50, unique=True)
    name = models.CharField("名称", max_length=100)
    description = models.CharField("描述", max_length=200)
    cost = models.BigIntegerField("价格", default=0)
    multiplier = models.FloatField("倍率", default=1.5)
    target_key = models.CharField("目标建筑键", max_length=50)

    class Meta:
        verbose_name = "升级卡"
        verbose_name_plural = "升级卡"

    def __str__(self):
        return self.name


class UserUpgradeCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    card = models.ForeignKey(UpgradeCard, on_delete=models.CASCADE, verbose_name="升级卡")
    owned = models.BooleanField("是否拥有", default=False)

    class Meta:
        unique_together = ("user", "card")
        verbose_name = "用户升级卡"
        verbose_name_plural = "用户升级卡"
