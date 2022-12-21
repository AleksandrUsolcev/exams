from django.db.models import F
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Question, Quiz, Variant


@receiver(post_save, sender=Variant)
@receiver(post_save, sender=Question)
@receiver(post_delete, sender=Variant)
@receiver(post_delete, sender=Question)
def quiz_update_revision(sender, instance, **kwargs):
    quiz = instance.quiz
    if quiz.active and quiz.visibility:
        Quiz.objects.filter(id=quiz.id).update(revision=F('revision') + 1)


@receiver(post_save, sender=Variant)
@receiver(post_delete, sender=Variant)
def question_active_change(sender, instance, **kwargs):
    empty_status = instance.quiz.empty_answers
    active = False
    if empty_status:
        variants_count = instance.question.variants.count()
        active = variants_count > 0
    else:
        variants = instance.question.variants.filter(correct=True)
        active = variants.exists()
    Question.objects.filter(id=instance.question.id).update(active=active)


@receiver(post_save, sender=Question)
@receiver(post_delete, sender=Question)
def quiz_active_change(sender, instance, **kwargs):
    active = instance.quiz.questions.filter(active=True).exists()
    Quiz.objects.filter(id=instance.quiz.id).update(active=active)
