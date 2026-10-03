from rest_framework import serializers

from .models import (
    APICallResult,
    APIIntegration,
    APITemplate,
    IntegrationAlert,
    IntegrationUsage,
    ScheduledAutomation,
)


class APIIntegrationSerializer(serializers.ModelSerializer):
    # Add a write-only field for authentication data
    authentication = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = APIIntegration
        fields = [  # noqa: RUF012
            "id",
            "name",
            "description",
            "type",
            "category",
            "endpoint",
            "method",
            "headers",
            "authentication",
            "parameters",
            "rate_limit",
            "retry_policy",
            "timeout",
            "status",
            "last_tested",
            "success_rate",
            "total_calls",
            "avg_response_time",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [  # noqa: RUF012
            "id",
            "created_at",
            "updated_at",
            "last_tested",
            "success_rate",
            "total_calls",
            "avg_response_time",
        ]

    def to_representation(self, instance):
        """Convert model instance to JSON representation"""
        representation = super().to_representation(instance)
        # Add decrypted authentication data to the representation
        representation["authentication"] = instance.get_auth_data()
        return representation


class APITemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = APITemplate
        fields = [  # noqa: RUF012
            "id",
            "name",
            "description",
            "category",
            "provider",
            "logo",
            "config_template",
            "popularity",
            "tags",
            "is_public",
            "documentation_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [  # noqa: RUF012
            "id",
            "created_at",
            "updated_at",
            "popularity",
        ]


class APICallResultSerializer(serializers.ModelSerializer):
    integration_name = serializers.CharField(source="integration.name", read_only=True)

    class Meta:
        model = APICallResult
        fields = [  # noqa: RUF012
            "id",
            "integration",
            "integration_name",
            "status",
            "response_data",
            "response_time",
            "error_message",
            "request_data",
            "timestamp",
        ]
        read_only_fields = ["id", "timestamp", "integration_name"]  # noqa: RUF012


class IntegrationUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationUsage
        fields = [  # noqa: RUF012
            "id",
            "integration",
            "date",
            "total_calls",
            "successful_calls",
            "failed_calls",
            "avg_response_time",
            "total_data_transferred",
        ]
        read_only_fields = ["id"]  # noqa: RUF012


class IntegrationAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationAlert
        fields = [  # noqa: RUF012
            "id",
            "integration",
            "severity",
            "message",
            "rule_triggered",
            "acknowledged",
            "acknowledged_by",
            "acknowledged_at",
            "resolved",
            "resolved_at",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]  # noqa: RUF012


class ScheduledAutomationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledAutomation
        fields = [  # noqa: RUF012
            "id",
            "name",
            "automation_type",
            "frequency",
            "cron_expression",
            "is_active",
            "config",
            "workflow",
            "last_run_at",
            "next_run_at",
            "last_result",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [  # noqa: RUF012
            "id",
            "last_run_at",
            "next_run_at",
            "last_result",
            "created_at",
            "updated_at",
        ]
