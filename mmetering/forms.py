from django import forms
from mmetering.tasks import send_contact_email_task


class ContactForm(forms.Form):
    name = forms.CharField(label="Name", required=True,
                           widget=forms.TextInput(attrs={'class': 'form-control col-md-7 col-xs-12'}))
    email = forms.EmailField(label="E-mail", required=True,
                             widget=forms.TextInput(attrs={'class': 'form-control col-md-7 col-xs-12'}))
    message = forms.CharField(
        label="Nachricht", widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control col-md-7 col-xs-12'}))

    def send_email(self):
        send_contact_email_task.delay(self.cleaned_data['name'], self.cleaned_data['email'],
                                      self.cleaned_data['message'])
