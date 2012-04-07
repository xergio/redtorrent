# -*- coding: utf-8 -*-
import django
from django.shortcuts import render_to_response
from django.http import HttpResponse
from tracker.models import AnnounceForm

import sys
import socket
import bencode
import redis
import struct

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
[06/Apr/2012 17:07:56] "GET /announce?info_hash=7%cc%08%1fG%60%a6%ab%05%1d%b8%d6%fa%d6%cd%2b%a1gl%98&peer_id=-TR2500-yg8gwwv9z5ao&port=51413&uploaded=0&downloaded=0&left=0&numwant=80&key=5085515f&compact=1&supportcrypto=1&event=started HTTP/1.1" 200 25

ping complete torrent 
[06/Apr/2012 17:08:57] "GET /announce?info_hash=7%cc%08%1fG%60%a6%ab%05%1d%b8%d6%fa%d6%cd%2b%a1gl%98&peer_id=-TR2500-yg8gwwv9z5ao&port=51413&uploaded=0&downloaded=0&left=0&numwant=80&key=5085515f&compact=1&supportcrypto=1 HTTP/1.1" 200 25


start nuevo cliente
[06/Apr/2012 17:59:56] "GET /announce?info_hash=7%cc%08%1fG%60%a6%ab%05%1d%b8%d6%fa%d6%cd%2b%a1gl%98&peer_id=M7-2-2--%c9d%e2%b2T%85%f8%93%ce%d9%ac%1d&port=15644&uploaded=0&downloaded=0&left=733261824&corrupt=0&key=6C7ED1C1&event=started&numwant=200&compact=1&no_peer_id=1&ipv6=fe80%3a%3a21c%3ab3ff%3afec5%3aa4a1 HTTP/1.1" 200 25

"""

def announce(request):
	try:
		ann = AnnounceForm(request.GET.dict())
		ann.ip = request.GET.get('ip') or request.GET.get('ipv6') or request.META.get('REMOTE_ADDR')

		if not ann.is_valid():
			raise Exception(ann.errors)

		qs = ann.cleaned_data
		r = redis.StrictRedis(host='localhost')
		
		if qs['event'] not in ['started', 'completed', 'stopped'] and len(qs['event'].strip()) > 0:
			raise Exception("event '%s' is invalid." % qs['event'])

		"""peers = []
		if request.GET.get('compact'):
			peers_l = ""
			for peer in peers:
				peers_l += struct.pack('>4sH', socket.inet_aton(peer['ip']), peer['port'])

		elif request.GET.get('no_peer_id'):
			peers_l = []
			for peer in peers:
				peers_ni.append({'ip': peer['ip'], 'port': peer['port']})

		else:
			peers_l = []
			for peer in peers:
				peers.append({'ip': peer['ip'], 'port': peer['port'], 'peer id': peer['peer_id']})"""
		peers_l = []

		return HttpResponse(
			bencode.bencode({
				'interval': 60,
				'peers': peers_l,
			}),
			mimetype = 'text/plain'
		)

	except:
		return response_fail(sys.exc_info()[1])


def scrape(request):
	#r = redis.StrictRedis(host='localhost')
	raise Exception(request.GET)
	return render_to_response('announce/scrape.html', {})


def response_fail(reason, xhr=False):
	raise Exception(reason)
	if not xhr:
		return HttpResponse(bencode.bencode({'failure reason': reason or 'unknown'}))

	r = HttpResponse(mimetype="text/xml")
	r.write("""<?xml version="1.0" encoding="UTF-8"?>""")
	r.write("""<result><msg>failure</msg></result>""")
	return r
