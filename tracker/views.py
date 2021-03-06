# -*- coding: utf-8 -*-
import django
from django.shortcuts import render_to_response
from django.http import HttpResponse
from tracker.models import AnnounceForm, ScrapeForm, Store

import sys
import socket
import bencode
import struct
import time
import redis

"""

http://bittorrent.org/beps/bep_0003.html
http://wiki.theory.org/BitTorrentSpecification#Tracker_HTTP.2FHTTPS_Protocol

/announce?
info_hash=gK%91d%e0%ec%fc%c0G%c1%0a%9bD8%85%a9%99%88%27%da&
peer_id=-TR2330-fnovv1t92c12&
port=51413&
uploaded=0&
downloaded=0&
left=0&
numwant=80&
key=6083d376&
compact=1&
supportcrypto=1&
event=started

/scrape?
info_hash=gK%91d%e0%ec%fc%c0G%c1%0a%9bD8%85%a9%99%88%27%da


start complete torrent
[07/Apr/2012 08:55:26] "GET /announce?info_hash=7%cc%08%1fG%60%a6%ab%05%1d%b8%d6%fa%d6%cd%2b%a1gl%98&peer_id=-TR2500-46xugddkkm12&port=51413&uploaded=0&downloaded=0&left=0&numwant=80&key=5085515f&compact=1&supportcrypto=1&event=started HTTP/1.1" 200 25

ping complete torrent 
[07/Apr/2012 08:56:27] "GET /announce?info_hash=7%cc%08%1fG%60%a6%ab%05%1d%b8%d6%fa%d6%cd%2b%a1gl%98&peer_id=-TR2500-46xugddkkm12&port=51413&uploaded=0&downloaded=0&left=0&numwant=80&key=5085515f&compact=1&supportcrypto=1 HTTP/1.1" 200 25


start nuevo cliente
[07/Apr/2012 08:56:01] "GET /announce?info_hash=7%cc%08%1fG%60%a6%ab%05%1d%b8%d6%fa%d6%cd%2b%a1gl%98&peer_id=M7-2-2--%c9d%e2%b2T%85%f8%93%ce%d9%ac%1d&port=15644&uploaded=0&downloaded=0&left=733261824&corrupt=0&key=6C7ED1C1&event=started&numwant=200&compact=1&no_peer_id=1&ipv6=fe80%3a%3a21c%3ab3ff%3afec5%3aa4a1 HTTP/1.1" 200 25

ping nuevo cliente
[07/Apr/2012 08:57:02] "GET /announce?info_hash=7%cc%08%1fG%60%a6%ab%05%1d%b8%d6%fa%d6%cd%2b%a1gl%98&peer_id=M7-2-2--%c9d%e2%b2T%85%f8%93%ce%d9%ac%1d&port=15644&uploaded=0&downloaded=0&left=733261824&corrupt=0&key=6C7ED1C1&numwant=200&compact=1&no_peer_id=1&ipv6=fe80%3a%3a21c%3ab3ff%3afec5%3aa4a1 HTTP/1.1" 200 25

"""

def announce(request):
	qs = request.GET.copy()
	qs.update({'ip': request.GET.get('ip') or request.META.get('REMOTE_ADDR')})
	ann = AnnounceForm(qs.dict())

	if not ann.is_valid():
		raise Exception(ann.errors)

	qs = ann.cleaned_data
	r = Store(host='localhost')
	r.set_info(qs['info_hash'], qs['peer_id'])


	# save ALL the params!
	r.save_peer(qs)


	# save ALL the states!
	if qs['event'] == 'completed':
		r.add_seeder()
		r.del_leecher()

	elif qs['event'] == 'stopped':
		r.del_seeder()
		r.del_leecher()
		r.delete_peer()

	else:
		if qs['left'] == 0:
			r.add_seeder()
			r.del_leecher()
		else:
			r.add_seeder()
			r.add_leecher()
	

	# get ALL the peers!
	nmembers = r.len_seeders()
	if nmembers < qs['numwant']:
		peer_ids = r.all_seeders()
	elif nmembers > 0:
		peer_ids = r.get_seeders(qs['numwant'])
	else:
		peer_ids = set()


	# clean ALL the peers!
	peers_data = []
	now = time.time()
	for peer_id in peer_ids:
		data = r.get_peer(peer_id)
		if not data or int(data['seen']) < now-(60*2):
			r.del_peer(peer_id)
		else:
			peers_data.append(data)


	# send ALL the peers
	if qs['compact']:
		peers_l = ""
		for peer in peers_data:
			peers_l += struct.pack('>4sH', socket.inet_aton(peer['ip']), int(peer['port']))

	elif qs['no_peer_id']:
		peers_l = []
		for peer in peers_data:
			peers_l.append({'ip': peer['ip'], 'port': int(peer['port'])})

	else:
		peers_l = []
		for peer in peers_data:
			peers_l.append({'peer id': peer['peer_id'], 'ip': peer['ip'], 'port': peer['port']})


	try:
		return HttpResponse(
			bencode.bencode({
				'interval': 60,
				'peers': peers_l
			}),
			content_type = 'text/plain'
		)

	except:
		return response_fail(sys.exc_info()[1])


def scrape(request):
	"""qs = request.GET.copy()
	scp = ScrapeForm(qs.dict())

	if not scp.is_valid():
		raise Exception(scp.errors)

	qs = scp.cleaned_data
	r = redis.Redis(host='localhost')
	seeders_key = 'redtracker:seeders:'+ qs['info_hash']
	leechers_key = 'redtracker:leechers:'+ qs['info_hash']

	return HttpResponse(
		bencode.bencode({
			'files': {
				qs['info_hash']: {
					'complete': r.sdiffstore('tmp', seeders_key, leechers_key), 
					'incomplete': r.scard(leechers_key), 
					'downloaded': 0 #TODO
				}
			}
		}),
		content_type = 'text/plain'
	)"""
	return render_to_response('tracker/scrape.html', {})


def response_fail(reason):
	return HttpResponse(
		bencode.bencode({'failure reason': reason or 'unknown'}), 
		content_type = 'text/plain'
	)


