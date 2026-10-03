from rest_framework import serializers

from .models import Integration, IntegrationExecution


class IntegrationSerializer(serializers.ModelSerializer):
    """Integration serializer"""

    class Meta:
        model = Integration
        fields = [  # noqa: RUF012
            "id",
            "name",
            "integration_type",
            "config",
            "is_active",
            "last_sync",
            "last_error",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [  # noqa: RUF012
            "id",
            "created_at",
            "updated_at",
            "last_sync",
            "last_error",
        ]

    def validate_config(self, value):
        """Validate configuration based on integration type"""
        integration_type = self.initial_data.get("integration_type")

        if integration_type == "azure_cosmosdb":
            required_fields = ["endpoint", "database_name"]
            for field in required_fields:
                if field not in value:
                    raise serializers.ValidationError(
                        f"{field} is required for Azure CosmosDB integration"
                    )
        elif integration_type == "azure_functions":
            required_fields = ["function_app_name"]
            for field in required_fields:
                if field not in value:
                    raise serializers.ValidationError(
                        f"{field} is required for Azure Functions integration"
                    )
        elif integration_type in ["zapier", "make"]:
            required_fields = ["webhook_url"]
            for field in required_fields:
                if field not in value:
                    raise serializers.ValidationError(
                        f"{field} is required for {integration_type} integration"
                    )

        return value


class IntegrationExecutionSerializer(serializers.ModelSerializer):
    """Integration execution serializer"""

    integration_name = serializers.CharField(source="integration.name", read_only=True)
    integration_type = serializers.CharField(
        source="integration.integration_type", read_only=True
    )

    class Meta:
        model = IntegrationExecution
        fields = [  # noqa: RUF012
            "id",
            "integration",
            "integration_name",
            "integration_type",
            "status",
            "request_data",
            "response_data",
            "error_message",
            "duration_ms",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]  # noqa: RUF012
