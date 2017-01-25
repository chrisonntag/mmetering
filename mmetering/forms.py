from django import forms
from mmetering.tasks import send_email_task


class ContactForm(forms.Form):
    name = forms.CharField(label="Name", required=True)
    email = forms.EmailField(label="Email", required=True)
    message = forms.CharField(
        label="Nachricht", widget=forms.Textarea(attrs={'rows': 5}))
    honeypot = forms.CharField(widget=forms.HiddenInput(), required=True)

    def send_email(self):
        # try to trick spammers by checking whether the honeypot field is
        # filled in; not super complicated/effective but it works
        if self.cleaned_data['honeypot']:
            return False
        send_email_task.delay(
            self.cleaned_data['name'],
            self.cleaned_data['email'],
            self.cleaned_data['message'])