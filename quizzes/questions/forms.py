from django import forms

from .models import Answer, Quiz


class QuizProcessForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(QuizProcessForm, self).__init__(*args, **kwargs)
        self.question = self.initial.get('question')
        self.quiz = self.initial.get('quiz')
        self.user = self.initial.get('user')
        if self.quiz.shuffle_variants:
            question_set = self.question.variants.all().order_by('?')
        else:
            question_set = self.question.variants.all()
        if self.question.many_correct:
            for variant in question_set:
                self.fields[str(variant.id)] = forms.BooleanField(
                    label=variant.text,
                    required=False
                )
        if self.question.one_correct:
            RADIOS = []
            for variant in question_set:
                RADIOS.append((str(variant.id), variant.text))
            self.fields['result'] = forms.ChoiceField(
                widget=forms.RadioSelect,
                choices=RADIOS,
            )

    def add_results(self, results):
        variants = self.question.variants.all()
        for_create = []
        for v_id in results:
            variant = variants.get(id=v_id)
            for_create.append(
                Answer(
                    user=self.user,
                    quiz=self.quiz,
                    quiz_revision=self.quiz.revision,
                    quiz_title=self.quiz.title,
                    question=self.question,
                    question_text=self.question.text,
                    variant=variant,
                    variant_text=variant.text,
                    correct=variant.correct
                )
            )
        Answer.objects.bulk_create(for_create)

    def answer(self):
        answer = Answer.objects.filter(
            user=self.user,
            quiz=self.quiz,
            quiz_revision=self.quiz.revision,
            question=self.question
        )
        if self.question.one_correct:
            result = [int(self.cleaned_data.get('result'))]
            if result and not answer.exists():
                self.add_results(result)
        if self.question.many_correct:
            results = []
            for variant_id in self.cleaned_data:
                status = self.cleaned_data.get(variant_id)
                if status is True:
                    results.append(int(variant_id))
            if results and not answer.exists():
                self.add_results(results)


class QuizAddUpdateView(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = '__all__'
        exclude = ('slug', 'author')
