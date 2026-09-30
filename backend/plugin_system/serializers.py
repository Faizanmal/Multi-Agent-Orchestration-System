from rest_framework import serializers

from .models import (
    CustomAgentPlugin,
    Plugin,
    PluginAPIKey,
    PluginInstallation,
    PluginReview,
)


class PluginSerializer(serializers.ModelSerializer):
    installations_count = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Plugin
        fields = '__all__'
    
    def get_installations_count(self, obj):
        return obj.installations.count()
    
    def get_reviews_count(self, obj):
        return obj.reviews.count()
    
    def get_avg_rating(self, obj):
        if obj.rating_count == 0:
            return 0.0
        return obj.rating


class PluginInstallationSerializer(serializers.ModelSerializer):
    plugin_name = serializers.CharField(source='plugin.name', read_only=True)
    plugin_version = serializers.CharField(source='plugin.version', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = PluginInstallation
        fields = '__all__'


class CustomAgentPluginSerializer(serializers.ModelSerializer):
    plugin_name = serializers.CharField(source='plugin.name', read_only=True)
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    agent_type = serializers.CharField(source='agent.agent_type', read_only=True)
    
    class Meta:
        model = CustomAgentPlugin
        fields = '__all__'


class PluginReviewSerializer(serializers.ModelSerializer):
    plugin_name = serializers.CharField(source='plugin.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = PluginReview
        fields = '__all__'


class PluginAPIKeySerializer(serializers.ModelSerializer):
    plugin_name = serializers.CharField(source='installation.plugin.name', read_only=True)
    
    class Meta:
        model = PluginAPIKey
        fields = '__all__'
        extra_kwargs = {  # noqa: RUF012
            'api_key': {'write_only': True},
            'api_secret': {'write_only': True}
        }
