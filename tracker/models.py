# -*- coding: utf-8 -*-
from django import forms
import redis
import time


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
	requirecrypto = forms.BooleanField(required=False, initial=False)

	def clean_event(self):
		event = self.cleaned_data['event'].strip()
		if event not in ['started', 'completed', 'stopped'] and len(event) > 0:
			raise forms.ValidationError("event '%s' is invalid." % event)
		return event


class ScrapeForm(forms.Form):
	info_hash = forms.CharField(max_length=100)


class Store(redis.Redis):
	
	def set_info(self, info_hash, peer_id):
		self.info_hash = info_hash
		self.peer_id = peer_id
		self.peer_key = "redtorrent:peer:%s" % self.peer_id
		self.seeders_key = "redtracker:seeders:%s" % self.info_hash
		self.leechers_key = "redtracker:leechers:%s" % self.info_hash
	
	def save_peer(self, data):
		data.update({'seen': int(time.time())})
		return self.hmset(self.peer_key, data)
		
	def delete_peer(self):
		return self.delete(self.peer_key)
		
	def get_peer(self, peer_id):
		return self.hgetall(u"redtorrent:peer:%s" % peer_id)
		
	def del_peer(self, peer_id):
		self.srem(self.seeders_key, peer_id)
		self.srem(self.leechers_key, peer_id)
		return self.delete(u"redtorrent:peer:%s" % peer_id)
		
	def add_seeder(self):
		return self.sadd(self.seeders_key, self.peer_id)
		
	def del_seeder(self):
		return self.srem(self.seeders_key, self.peer_id)
		
	def add_leecher(self):
		return self.sadd(self.leechers_key, self.peer_id)
		
	def del_leecher(self):
		return self.srem(self.leechers_key, self.peer_id)
		
	def len_seeders(self):
		return self.scard(self.seeders_key)
		
	def len_leechers(self):
		return self.scard(self.leechers_key)
		
	def all_seeders(self):
		return self.smembers(self.seeders_key)
		
	def get_seeders(self, num=50):
		peer_ids = set()
		i = 0
		while len(peer_ids) < num and i < 1000:
			peer_ids.add(self.srandmember(self.seeders_key))
			i += 1
		return peer_ids
		
		
		
		