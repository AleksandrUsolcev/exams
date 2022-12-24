from rest_framework import serializers

from questions.models import Quiz


class QuizSerializer(serializers.ModelSerializer):

    value = serializers.SerializerMethodField('get_value')
    theme = serializers.SlugRelatedField(slug_field='title', read_only=True)

    class Meta:
        model = Quiz
        fields = ('value', 'slug', 'theme')

    def get_value(self, obj):
        return obj.title
