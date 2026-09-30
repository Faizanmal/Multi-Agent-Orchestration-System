from rest_framework import serializers

from .models import Dashboard, Report, ReportTemplate, Widget


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']  # noqa: RUF012

class ReportTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplate
        fields = '__all__'
        read_only_fields = ['id', 'created_at']  # noqa: RUF012

class DashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dashboard
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']  # noqa: RUF012

class WidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Widget
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']  # noqa: RUF012
