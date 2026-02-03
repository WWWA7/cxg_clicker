import asyncio
import random
from django.utils import timezone
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async
from django.core.cache import cache
from .services import tick, compute_rates, get_user_buildings, get_price, get_building_multiplier
from .models import GameState

class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
            return
        self.user = self.scope["user"]
        self.group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        self.running = True
        asyncio.create_task(self.push_loop())

    async def disconnect(self, close_code):
        self.running = False
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def push_loop(self):
        while self.running:
            payload = await sync_to_async(build_state_payload)(self.user)
            await self.send_json({"type": "state", **payload})
            await asyncio.sleep(2)

def build_state_payload(user):
    state = tick(user)
    now = timezone.now()

    if state.buff_ends_at and now > state.buff_ends_at:
        state.buff_multiplier = 1.0
        state.buff_ends_at = None
        state.save()

    if not state.event_expires_at or now > state.event_expires_at:
        if not state.last_event_at or (now - state.last_event_at).total_seconds() > 60:
            if random.random() < 0.05:
                state.event_id = int(now.timestamp())
                state.event_multiplier = 2.0
                state.event_expires_at = now + timezone.timedelta(seconds=20)
                state.last_event_at = now
                state.save()

    per_second, per_click = compute_rates(user, state.upgrade_level, state.buff_multiplier)

    buildings = []
    for b, ub in get_user_buildings(user):
        mult = get_building_multiplier(user, b)
        buildings.append({
            "key": b.key,
            "amount": ub.amount,
            "price": get_price(b, ub.amount),
            "per_second_total": b.base_per_second * ub.amount * mult,
            "per_click_total": b.base_per_click * ub.amount * mult,
            "per_second_next": b.base_per_second * (ub.amount + 1) * mult,
            "per_click_next": b.base_per_click * (ub.amount + 1) * mult,
        })

    leaderboard = cache.get("leaderboard")
    if leaderboard is None:
        top = GameState.objects.order_by("-apples_total")[:5]
        leaderboard = [{"name": t.user.username, "score": t.apples_total} for t in top]
        cache.set("leaderboard", leaderboard, 10)

    return {
        "apples": state.apples,
        "apples_total": state.apples_total,
        "clicks": state.clicks,
        "upgrade_level": state.upgrade_level,
        "per_second": int(per_second),
        "per_click": int(per_click),
        "buildings": buildings,
        "leaderboard": leaderboard,
        "event": {
            "active": bool(state.event_expires_at and now < state.event_expires_at),
            "id": state.event_id,
            "multiplier": state.event_multiplier if state.event_expires_at else 1.0,
            "expires_at": state.event_expires_at.isoformat() if state.event_expires_at else None
        }
    }
