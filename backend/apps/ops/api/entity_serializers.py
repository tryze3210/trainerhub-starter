from rest_framework import serializers


class AdminEntityRelationshipSerializer(serializers.Serializer):
    entity_type = serializers.CharField()
    entity_id = serializers.CharField()
    label = serializers.CharField()
    href = serializers.CharField()


class AdminEntityDetailSerializer(serializers.Serializer):
    entity_type = serializers.CharField()
    entity_id = serializers.CharField()
    title = serializers.CharField()
    status = serializers.CharField()
    primary = serializers.DictField()
    payload = serializers.DictField()
    relationships = AdminEntityRelationshipSerializer(many=True)
    raw = serializers.DictField()
