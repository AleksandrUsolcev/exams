from itertools import chain
from operator import attrgetter

from django.db.models import (BooleanField, Case, Count, ExpressionWrapper, F,
                              IntegerField, Q, When)

from .models import Quiz


def get_quizzes_with_progress(user: object, theme_slug: str) -> object:
    if user.is_authenticated:
        query_with_user_progress = Quiz.objects.filter(
            theme__slug=theme_slug,
            progress__user=user
        ).prefetch_related('progress').annotate(
            questions_count=Count('questions'),
            current_stage=F('progress__stage'),
            passed=Case(
                When(progress__passed__isnull=False, then=True),
                default=False,
                output_field=BooleanField()
            ),
            percentage=ExpressionWrapper(
                F('progress__answers') * 100 / Count('questions'),
                output_field=IntegerField()
            )
        )
        query_without_user = Quiz.objects.filter(
            Q(theme__slug=theme_slug) &
            ~Q(id__in=query_with_user_progress.values_list('id', flat=True))
        ).annotate(questions_count=Count('questions'))
        queryset = sorted(
            list(chain(query_without_user, query_with_user_progress)),
            key=attrgetter('created'), reverse=True
        )
        return queryset
    queryset = Quiz.objects.filter(theme__slug=theme_slug).annotate(
        questions_count=Count('questions')).order_by('-created')
    return queryset
