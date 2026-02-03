from django.utils import timezone
from .models import Building, GameState, UserBuilding, Achievement, UserAchievement, UpgradeCard, UserUpgradeCard
from .data import BUILDINGS, ACHIEVEMENTS, UPGRADE_CARDS
from types import SimpleNamespace
import math
import random

OFFLINE_CAP_SECONDS = 8 * 3600


def ensure_buildings():
    existing = set(Building.objects.values_list("key", flat=True))
    missing = [b for b in BUILDINGS if b["key"] not in existing]
    if not missing:
        return
    Building.objects.bulk_create([
        Building(
            key=b["key"],
            name=b["name"],
            flavor=b["flavor"],
            base_price=b["base_price"],
            base_per_second=b["base_per_second"],
            base_per_click=b["base_per_click"],
        )
        for b in missing
    ])


def ensure_achievements():
    existing = set(Achievement.objects.values_list("key", flat=True))
    missing = [a for a in ACHIEVEMENTS if a["key"] not in existing]
    if not missing:
        return
    Achievement.objects.bulk_create([
        Achievement(
            key=a["key"],
            name=a["name"],
            rule=a["rule"],
            kind=a["kind"],
            threshold=a["threshold"],
            building_key=a.get("building_key", ""),
            reward_apples=a.get("reward_apples", 0),
            reward_multiplier=a.get("reward_multiplier", 1.0),
            reward_seconds=a.get("reward_seconds", 0),
        )
        for a in missing
    ])


def ensure_upgrades():
    existing = set(UpgradeCard.objects.values_list("key", flat=True))
    missing = [u for u in UPGRADE_CARDS if u["key"] not in existing]
    if not missing:
        return
    UpgradeCard.objects.bulk_create([
        UpgradeCard(
            key=u["key"],
            name=u["name"],
            description=u["description"],
            cost=u["cost"],
            multiplier=u["multiplier"],
            target_key=u["target_key"],
        )
        for u in missing
    ])


def get_or_create_state(user):
    state, _ = GameState.objects.get_or_create(user=user)
    return state


def get_user_buildings(user):
    ensure_buildings()
    buildings = list(Building.objects.all())
    user_buildings = {ub.building_id: ub for ub in UserBuilding.objects.filter(user=user)}
    result = []
    for b in buildings:
        ub = user_buildings.get(b.id)
        if not ub:
            ub = SimpleNamespace(amount=0)
        result.append((b, ub))
    return result


def get_building_multiplier(user, building):
    mult = 1.0
    for card in UserUpgradeCard.objects.filter(user=user, owned=True, card__target_key=building.key):
        mult *= card.card.multiplier
    return mult


def compute_rates(user, upgrade_level, buff_multiplier=1.0):
    total_per_second = 0.0
    total_per_click = 1.0
    for b, ub in get_user_buildings(user):
        mult = get_building_multiplier(user, b)
        total_per_second += b.base_per_second * ub.amount * mult
        total_per_click += b.base_per_click * ub.amount * mult
    total_per_second *= math.pow(1.03, upgrade_level + 1)
    total_per_second *= buff_multiplier
    total_per_click *= buff_multiplier
    return total_per_second, total_per_click


def tick(user):
    state = get_or_create_state(user)
    now = timezone.now()
    changed = False

    if state.buff_ends_at and now > state.buff_ends_at:
        state.buff_multiplier = 1.0
        state.buff_ends_at = None
        changed = True

    delta = (now - state.last_tick).total_seconds()
    if delta > 0:
        delta = min(delta, OFFLINE_CAP_SECONDS)
        per_second, _ = compute_rates(user, state.upgrade_level, state.buff_multiplier)
        gained = int(per_second * delta)
        if gained:
            state.apples += gained
            state.apples_total += gained
        state.last_tick = now
        changed = True

    if not state.event_expires_at or now > state.event_expires_at:
        if not state.last_event_at or (now - state.last_event_at).total_seconds() > 60:
            if random.random() < 0.05:
                state.event_id = int(now.timestamp())
                state.event_multiplier = 2.0
                state.event_expires_at = now + timezone.timedelta(seconds=20)
                state.last_event_at = now
                changed = True

    if changed:
        state.save()
    return state


def get_price(building, owned):
    return int(building.base_price * (building.price_growth ** owned))


def check_achievements(user, state):
    ensure_achievements()
    unlocked = []
    for a in Achievement.objects.all():
        ua, _ = UserAchievement.objects.get_or_create(user=user, achievement=a)
        if ua.unlocked:
            continue
        ok = False
        if a.kind == "apples_total" and state.apples_total >= a.threshold:
            ok = True
        elif a.kind == "clicks" and state.clicks >= a.threshold:
            ok = True
        elif a.kind == "building":
            b = Building.objects.filter(key=a.building_key).first()
            if b:
                ub, _ = UserBuilding.objects.get_or_create(user=user, building=b)
                if ub.amount >= a.threshold:
                    ok = True
        if ok:
            ua.unlocked = True
            ua.save()
            state.apples += a.reward_apples
            state.apples_total += a.reward_apples
            if a.reward_multiplier > 1.0 and a.reward_seconds > 0:
                state.buff_multiplier = max(state.buff_multiplier, a.reward_multiplier)
                state.buff_ends_at = timezone.now() + timezone.timedelta(seconds=a.reward_seconds)
            state.save()
            unlocked.append(a)
    return unlocked
