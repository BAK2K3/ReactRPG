from rest_framework import serializers
from .models import Codex


class CodexSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Codex
        fields = ['name', 'alpha_name', 'type', 'base_hp', 'base_attack', 'base_defense',
                  'base_speed', 'image', 'paid', 'min_level']
