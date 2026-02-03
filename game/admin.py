from django.contrib import admin
from .models import Building, GameState, UserBuilding, Achievement, UserAchievement

admin.site.site_header = "雌小鬼点点乐后台"
admin.site.site_title = "雌小鬼后台"
admin.site.index_title = "管理中心"


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "base_price", "base_per_second", "base_per_click", "price_growth")
    list_display = ("key", "name", "base_price", "base_per_second", "base_per_click", "price_growth")


@admin.register(GameState)
class GameStateAdmin(admin.ModelAdmin):
    list_display = ("rank", "user", "apples_total", "apples", "clicks", "upgrade_level", "last_tick")
    ordering = ("-apples_total",)
    list_per_page = 50

    def rank(self, obj):
        return GameState.objects.filter(apples_total__gt=obj.apples_total).count() + 1

    rank.short_description = "排名"


@admin.register(UserBuilding)
class UserBuildingAdmin(admin.ModelAdmin):
    list_display = ("user", "building", "amount")


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "kind", "threshold", "building_key")


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ("user", "achievement", "unlocked")
