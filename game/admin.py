from django.contrib import admin
from .models import Building, GameState, UserBuilding, Achievement, UserAchievement

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "base_price", "base_per_second", "base_per_click", "price_growth")

@admin.register(GameState)
class GameStateAdmin(admin.ModelAdmin):
    list_display = ("user", "apples", "apples_total", "clicks", "upgrade_level", "last_tick")

@admin.register(UserBuilding)
class UserBuildingAdmin(admin.ModelAdmin):
    list_display = ("user", "building", "amount")

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "kind", "threshold", "building_key")

@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ("user", "achievement", "unlocked")
