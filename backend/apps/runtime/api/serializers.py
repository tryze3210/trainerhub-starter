from rest_framework import serializers


class RuntimeHealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    service = serializers.CharField()
    timestamp = serializers.CharField()


class RuntimeCheckSerializer(serializers.Serializer):
    name = serializers.CharField()
    status = serializers.CharField()
    details = serializers.CharField()


class RuntimeReadinessSerializer(serializers.Serializer):
    status = serializers.CharField()
    checks = RuntimeCheckSerializer(many=True)


class RuntimeConfigSerializer(serializers.Serializer):
    env = serializers.CharField()
    debug = serializers.BooleanField()
    allowed_hosts = serializers.ListField(child=serializers.CharField())
    postgres = serializers.DictField()
    redis_url = serializers.CharField()
    celery = serializers.DictField()
    storage = serializers.DictField()


class CachePingSerializer(serializers.Serializer):
    status = serializers.CharField()
    backend = serializers.CharField()
    key = serializers.CharField()
