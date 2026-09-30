from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path(
        "campaigns/",
        views.NotificationCampaignListCreateView.as_view(),
        name="campaigns",
    ),
    path(
        "campaigns/<uuid:pk>/",
        views.NotificationCampaignDetailView.as_view(),
        name="campaign_detail",
    ),
    path("campaigns/<uuid:pk>/send/", views.send_campaign_view, name="send_campaign"),
    path(
        "templates/",
        views.NotificationTemplateListCreateView.as_view(),
        name="templates",
    ),
    path("rules/", views.NotificationRuleListCreateView.as_view(), name="rules"),
    path("stats/", views.notification_stats_view, name="stats"),
    path(
        "preferences/", views.NotificationPreferenceView.as_view(), name="preferences"
    ),
    path(
        "subscriptions/",
        views.NotificationSubscriptionListCreateView.as_view(),
        name="subscriptions",
    ),
]
