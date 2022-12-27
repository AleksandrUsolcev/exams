from rest_framework import serializers

from questions.models import Exam


class ExamSerializer(serializers.ModelSerializer):

    value = serializers.SerializerMethodField('get_value')
    category = serializers.SlugRelatedField(slug_field='title', read_only=True)

    class Meta:
        model = Exam
        fields = ('value', 'slug', 'category')

    def get_value(self, obj):
        return obj.title
