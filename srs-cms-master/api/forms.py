from django import forms


class AdminImportFileForm(forms.Form):
    file = forms.FileField()
