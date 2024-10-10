from django.shortcuts import render, redirect
from django import forms
from .models import Time, Jogador

class TimeForm(forms.ModelForm):
    class Meta:
        model = Time
        fields = ['nome', 'sigla', 'tecnico']

    # Campo adicional para selecionar jogadores titulares e banco
    jogadores_titulares = forms.ModelMultipleChoiceField(
        queryset=Jogador.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Jogadores Titulares"
    )
    jogadores_banco = forms.ModelMultipleChoiceField(
        queryset=Jogador.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Jogadores Banco",
        required=False
    )
