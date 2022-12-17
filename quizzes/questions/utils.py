from django.db.models import (BooleanField, Case, Count, ExpressionWrapper, F,
                              IntegerField, When)

from .models import Quiz


def get_quizzes_with_progress(user: object, theme_slug: str) -> object:
    if user.is_authenticated:
        return Quiz.objects.filter(
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
        ).order_by('-created')
    return Quiz.objects.filter(
        theme__slug=theme_slug).annotate(
        questions_count=Count('questions')
    ).order_by('-created')
