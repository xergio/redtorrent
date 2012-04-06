
from django.shortcuts import render_to_response
from django.http import HttpResponse

import sys
import socket
import bencode
import redis
import struct

"""
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

[06/Apr/2012 06:08:29] "GET /announce?info_hash=7%cc%08%1fG%60%a6%ab%05%1d%b8%d6%fa%d6%cd%2b%a1gl%98&peer_id=-TR2500-1u2n01ylhvvp&port=51413&uploaded=0&downloaded=0&left=0&numwant=80&key=90ecacb&compact=1&supportcrypto=1&event=started HTTP/1.1" 200 25
[06/Apr/2012 06:09:30] "GET /announce?info_hash=7%cc%08%1fG%60%a6%ab%05%1d%b8%d6%fa%d6%cd%2b%a1gl%98&peer_id=-TR2500-1u2n01ylhvvp&port=51413&uploaded=0&downloaded=0&left=0&numwant=80&key=90ecacb&compact=1&supportcrypto=1 HTTP/1.1" 200 25
"""

def announce(request):
	try:
		r = redis.StrictRedis(host='localhost')
		info = {}

		info_hash = request.GET.get('info_hash', '')
		if len(info_hash) < 20:
			raise Exception("problem with info hash.")
		info['info_hash'] = info_hash

		if not request.GET.get('peer_id', ''):
			raise Exception('problem with peer id.')
		info['peer_id'] = request.GET['peer_id']

		info['ip'] = request.GET.get('ip') or request.META.get('REMOTE_ADDR')
		try:
			socket.gethostbyname(info['ip'])
		except:
			raise Exception("unable to resolve host name '%s'." % info['ip'])

		for key in ['uploaded', 'downloaded', 'port', 'left']:
			if request.GET.has_key(key):
				try:
					info[key] = int(request.GET[key])
				except ValueError:
					raise Exception("argument '%s' has an incorrect type." % key)
			else:
				raise Exception("argument '%s' not specified." % key)

		event = request.GET.get('event', '')
		if event not in ['started', 'completed', 'stopped'] and len(event.strip()) > 0:
			raise Exception("event '%s' is invalid." % event)

		numwant = request.GET.get('numwant', 50)
		try:
			numwant = int(numwant)
		except ValueError:
			numwant = 50

		peers = []
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
				peers.append({'ip': peer['ip'], 'port': peer['port'], 'peer id': peer['peer_id']})

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
