import random
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import RegisterForm
from .models import Building, UserBuilding, GameState, Achievement, UserAchievement, UpgradeCard, UserUpgradeCard
from .services import (
    ensure_buildings, ensure_achievements, ensure_upgrades,
    get_user_buildings, compute_rates, tick, get_price,
    check_achievements, get_building_multiplier
)

def login_view(request):
    if request.user.is_authenticated:
        return redirect("/")
    error = None
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("/")
        error = "账号或密码错误"
    return render(request, "auth/login.html", {"error": error})

def logout_view(request):
    logout(request)
    return redirect("/login/")

def register_view(request):
    if request.user.is_authenticated:
        return redirect("/")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            login(request, user)
            return redirect("/")
    else:
        form = RegisterForm()
    return render(request, "auth/register.html", {"form": form})

@login_required
def index(request):
    ensure_buildings()
    ensure_achievements()
    ensure_upgrades()
    state = tick(request.user)

    buildings = []
    for b, ub in get_user_buildings(request.user):
        mult = get_building_multiplier(request.user, b)
        buildings.append({
            "key": b.key,
            "name": b.name,
            "flavor": b.flavor,
            "price": get_price(b, ub.amount),
            "amount": ub.amount,
            "per_second_total": b.base_per_second * ub.amount * mult,
            "per_click_total": b.base_per_click * ub.amount * mult,
            "per_second_next": b.base_per_second * (ub.amount + 1) * mult,
            "per_click_next": b.base_per_click * (ub.amount + 1) * mult,
        })

    per_second, per_click = compute_rates(request.user, state.upgrade_level, state.buff_multiplier)
    upgrade_price = int(200000 * (1.2 ** state.upgrade_level))

    ua_map = {ua.achievement_id: ua.unlocked for ua in UserAchievement.objects.filter(user=request.user)}
    achievements = [{"name": a.name, "rule": a.rule, "unlocked": ua_map.get(a.id, False)} for a in Achievement.objects.all()]

    cards = []
    for card in UpgradeCard.objects.all():
        owned = UserUpgradeCard.objects.filter(user=request.user, card=card, owned=True).exists()
        cards.append({
            "key": card.key,
            "name": card.name,
            "desc": card.description,
            "cost": card.cost,
            "multiplier": card.multiplier,
            "target_key": card.target_key,
            "owned": owned,
        })

    return render(request, "game/index.html", {
        "state": state,
        "buildings": buildings,
        "per_second": int(per_second),
        "per_click": int(per_click),
        "upgrade_price": upgrade_price,
        "achievements": achievements,
        "cards": cards,
    })

@login_required
def state_api(request):
    state = tick(request.user)

    if state.buff_ends_at and timezone.now() > state.buff_ends_at:
        state.buff_multiplier = 1.0
        state.buff_ends_at = None
        state.save()

    now = timezone.now()
    if not state.event_expires_at or now > state.event_expires_at:
        if not state.last_event_at or (now - state.last_event_at).total_seconds() > 60:
            if random.random() < 0.05:
                state.event_id = int(now.timestamp())
                state.event_multiplier = 2.0
                state.event_expires_at = now + timezone.timedelta(seconds=20)
                state.last_event_at = now
                state.save()

    per_second, per_click = compute_rates(request.user, state.upgrade_level, state.buff_multiplier)

    buildings = []
    for b, ub in get_user_buildings(request.user):
        mult = get_building_multiplier(request.user, b)
        buildings.append({
            "key": b.key,
            "amount": ub.amount,
            "price": get_price(b, ub.amount),
            "per_second_total": b.base_per_second * ub.amount * mult,
            "per_click_total": b.base_per_click * ub.amount * mult,
            "per_second_next": b.base_per_second * (ub.amount + 1) * mult,
            "per_click_next": b.base_per_click * (ub.amount + 1) * mult,
        })

    return JsonResponse({
        "apples": state.apples,
        "apples_total": state.apples_total,
        "clicks": state.clicks,
        "upgrade_level": state.upgrade_level,
        "per_second": int(per_second),
        "per_click": int(per_click),
        "buildings": buildings,
        "event": {
            "active": bool(state.event_expires_at and now < state.event_expires_at),
            "id": state.event_id,
            "multiplier": state.event_multiplier if state.event_expires_at else 1.0,
            "expires_at": state.event_expires_at.isoformat() if state.event_expires_at else None
        }
    })

@login_required
@require_POST
def click_batch_api(request):
    state = tick(request.user)
    count = int(request.POST.get("count", "0"))
    per_second, per_click = compute_rates(request.user, state.upgrade_level, state.buff_multiplier)
    add = int(per_click) * count
    state.apples += add
    state.apples_total += add
    state.clicks += count
    state.save()
    unlocked = check_achievements(request.user, state)
    return JsonResponse({
        "ok": True,
        "apples": state.apples,
        "apples_total": state.apples_total,
        "clicks": state.clicks,
        "per_click": int(per_click),
        "per_second": int(per_second),
        "unlocked": [{"name": a.name, "rule": a.rule} for a in unlocked],
    })

@login_required
@require_POST
def buy_api(request):
    ensure_buildings()
    state = tick(request.user)
    key = request.POST.get("key")
    building = Building.objects.filter(key=key).first()
    if not building:
        return JsonResponse({"ok": False, "error": "建筑不存在"}, status=400)
    ub, _ = UserBuilding.objects.get_or_create(user=request.user, building=building)
    price = get_price(building, ub.amount)
    if state.apples < price:
        return JsonResponse({"ok": False, "error": "点数不足"}, status=400)

    state.apples -= price
    ub.amount += 1
    ub.save()
    state.save()

    mult = get_building_multiplier(request.user, building)
    next_price = get_price(building, ub.amount)
    per_second, per_click = compute_rates(request.user, state.upgrade_level, state.buff_multiplier)
    unlocked = check_achievements(request.user, state)

    return JsonResponse({
        "ok": True,
        "apples": state.apples,
        "amount": ub.amount,
        "next_price": next_price,
        "per_second_total": building.base_per_second * ub.amount * mult,
        "per_click_total": building.base_per_click * ub.amount * mult,
        "per_second_next": building.base_per_second * (ub.amount + 1) * mult,
        "per_click_next": building.base_per_click * (ub.amount + 1) * mult,
        "per_second": int(per_second),
        "per_click": int(per_click),
        "unlocked": [{"name": a.name, "rule": a.rule} for a in unlocked],
    })

@login_required
@require_POST
def upgrade_api(request):
    state = tick(request.user)
    price = int(200000 * (1.2 ** state.upgrade_level))
    if state.apples < price:
        return JsonResponse({"ok": False, "error": "点数不足"}, status=400)
    state.apples -= price
    state.upgrade_level += 1
    state.save()

    per_second, per_click = compute_rates(request.user, state.upgrade_level, state.buff_multiplier)

    return JsonResponse({
        "ok": True,
        "apples": state.apples,
        "upgrade_level": state.upgrade_level,
        "next_price": int(200000 * (1.2 ** state.upgrade_level)),
        "per_second": int(per_second),
        "per_click": int(per_click),
    })

@login_required
@require_POST
def upgrade_card_api(request):
    ensure_upgrades()
    state = tick(request.user)
    key = request.POST.get("key")
    card = UpgradeCard.objects.filter(key=key).first()
    if not card:
        return JsonResponse({"ok": False, "error": "升级卡不存在"}, status=400)
    uc, _ = UserUpgradeCard.objects.get_or_create(user=request.user, card=card)
    if uc.owned:
        return JsonResponse({"ok": False, "error": "已拥有该升级卡"}, status=400)
    if state.apples < card.cost:
        return JsonResponse({"ok": False, "error": "点数不足"}, status=400)

    state.apples -= card.cost
    state.save()
    uc.owned = True
    uc.save()

    per_second, per_click = compute_rates(request.user, state.upgrade_level, state.buff_multiplier)

    return JsonResponse({"ok": True, "apples": state.apples, "key": card.key, "per_second": int(per_second), "per_click": int(per_click)})

@login_required
@require_POST
def event_claim_api(request):
    state = tick(request.user)
    event_id = request.POST.get("event_id")
    now = timezone.now()

    if not state.event_expires_at or now > state.event_expires_at:
        return JsonResponse({"ok": False, "error": "事件已过期"}, status=400)
    if str(state.event_id) != str(event_id):
        return JsonResponse({"ok": False, "error": "事件无效"}, status=400)

    state.buff_multiplier = state.event_multiplier
    state.buff_ends_at = now + timezone.timedelta(seconds=15)
    state.event_expires_at = None
    state.event_id = None
    state.save()

    return JsonResponse({"ok": True, "multiplier": state.buff_multiplier, "seconds": 15})
