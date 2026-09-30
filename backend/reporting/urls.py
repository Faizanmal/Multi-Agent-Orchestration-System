from django.urls import path

from . import views

app_name = "reporting"

urlpatterns = [
    path("reports/", views.ReportListCreateView.as_view(), name="reports"),
    path("reports/<uuid:pk>/", views.ReportDetailView.as_view(), name="report_detail"),
    path(
        "reports/<uuid:pk>/generate/",
        views.generate_report_view,
        name="generate_report",
    ),
    path("reports/<uuid:pk>/export/", views.export_report_view, name="export_report"),
    path("templates/", views.ReportTemplateListView.as_view(), name="templates"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("widgets/", views.WidgetListCreateView.as_view(), name="widgets"),
]
