from django import forms

class NameForm(forms.Form):
    fname = forms.CharField(label='Entrer un(e) ville, code postal, code département', max_length=100)