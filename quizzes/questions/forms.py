from django import forms


class QuizProcessForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(QuizProcessForm, self).__init__(*args, **kwargs)
        question = self.initial.get('question')
        for variant in question.variants.all():
            self.fields[f'variant-{variant.id}'] = forms.BooleanField(
                label=variant.text,
                required=False
            )

    def send_email(self):
        # send email using the self.cleaned_data dictionary
        pass
