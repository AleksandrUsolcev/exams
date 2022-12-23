from rest_framework import serializers

from questions.models import Quiz


class QuizSerializer(serializers.ModelSerializer):

    value = serializers.SerializerMethodField('get_value')

    class Meta:
        model = Quiz
        fields = ('value', 'slug')

    def get_value(self, obj):
        return obj.title
