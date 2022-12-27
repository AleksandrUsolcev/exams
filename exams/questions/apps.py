from django.apps import AppConfig


class QuestionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'questions'
    verbose_name = 'Тестирование'

    def ready(self):
        import questions.signals
