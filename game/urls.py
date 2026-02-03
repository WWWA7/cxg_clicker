from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="game_index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),

    path("api/state/", views.state_api, name="state_api"),
    path("api/click-batch/", views.click_batch_api, name="click_batch_api"),
    path("api/buy/", views.buy_api, name="buy_api"),
    path("api/upgrade/", views.upgrade_api, name="upgrade_api"),
    path("api/upgrade-card/", views.upgrade_card_api, name="upgrade_card_api"),
    path("api/event-claim/", views.event_claim_api, name="event_claim_api"),
]
