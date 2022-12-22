from django.db.models import F
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Question, Variant


@receiver(post_save, sender=Variant)
@receiver(post_save, sender=Question)
@receiver(post_delete, sender=Variant)
@receiver(post_delete, sender=Question)
def quiz_update_revision(sender, instance, **kwargs):
    if instance.quiz.active and instance.quiz.visibility:
        instance.quiz.revision = F('revision') + 1
        instance.quiz.save()


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
    instance.question.active = active
    instance.question.save()
    active = instance.quiz.questions.filter(
        active=True, visibility=True).exists()
    instance.quiz.active = active
    instance.quiz.save()


@receiver(post_save, sender=Question)
@receiver(post_delete, sender=Question)
def quiz_active_change(sender, instance, raw, **kwargs):
    empty_status = instance.quiz.empty_answers
    active = False
    quiz_active = instance.quiz.questions.filter(
        active=True, visibility=True).exists()
    if instance.variants.count():
        if (instance.one_correct
                and instance.variants.filter(correct=True).count() == 1):
            active = True
        elif instance.many_correct:
            if empty_status:
                active = True
            else:
                variants = instance.variants.filter(correct=True)
                active = variants.exists()
    Question.objects.filter(id=instance.id).update(active=active)
    instance.quiz.active = quiz_active
    instance.quiz.save()
