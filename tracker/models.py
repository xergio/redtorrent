# -*- coding: utf-8 -*-
from django import forms

class AnnounceForm(forms.Form):
	info_hash = forms.CharField(max_length=100)
	peer_id = forms.CharField(max_length=100)
	port = forms.IntegerField()
	uploaded = forms.IntegerField()
	downloaded = forms.IntegerField()
	left = forms.IntegerField()
	compact = forms.BooleanField(required=False, initial=False)
	no_peer_id = forms.BooleanField(required=False, initial=False)
	event = forms.CharField(max_length=9, required=False)
	ip = forms.CharField(max_length=100, required=False)
	numwant = forms.IntegerField(required=False, initial=50)
	key = forms.CharField(max_length=20, required=False)
	trackerid = forms.CharField(max_length=20, required=False)
	supportcrypto = forms.BooleanField(required=False, initial=False)

	def clean_event(self):
		data = self.cleaned_data['event']
		if data not in ['started', 'completed', 'stopped'] and len(data.strip()) > 0:
			raise forms.ValidationError("event '%s' is invalid." % data)
		return data
