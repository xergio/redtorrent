
from django.shortcuts import render_to_response

import sys
import socket
import benc
import redis

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
"""

def announce(request):
    #r = redis.StrictRedis(host='localhost')
    try:
	    info = {}

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
	        raise Exception("event '%s' is invalid" % event)

	    # is the announce method allowed ?
	    if REQUIRE_ANNOUNCE_PROTOCOL == 'no_peer_id':
	        if not request.GET.get('compact') and not request.GET.get('no_peer_id'):
	            return _fail("standard announces not allowed; use no_peer_id or compact option")
	    elif REQUIRE_ANNOUNCE_PROTOCOL == 'compact':
	        if not request.GET.get('compact'):
	            return _fail("tracker requires use of compact option")

	    info_hash = request.GET.get('info_hash', '')
	    if len(info_hash) < 20 or not request.GET.get('peer_id'):
	        return _fail("invalid request")
	    try:
	        info_hash = info_hash.encode('iso-8859-1').encode('hex')
	    except:
	        return _fail("invalid request")
	    args['peer_id'] = request.GET['peer_id']
	    torrent_id = Torrent.objects.filter(info_hash=info_hash).values('id')
	    if not torrent_id:
	        return _fail("no such torrent")
	    else:
	        torrent_id = torrent_id[0]['id']

	    # calculate announce interval
	    now = datetime.datetime.now()

	    mc = memcache.Client([MEMCACHE], debug=0)
	    peers = mc.get('peers')

	    if not peers:
	        peers = []

	    if not OPEN_TRACKER:
	        dwns = len([p for p in peers if p['user_id'] == u.id and p['expire_time']>now])
	        cur_dwns = u.attrs.get('max_sim_dwn', 2)
	        if dwns >= cur_dwns and cur_dwns != 0:
	            return _fail("maximum number of simultaneous downloads reached: %s"% dwns)

	    num_peers = len([p for p in peers if p['expire_time']>now])
	    announce_rate = len([p for p in peers if p['update_time']>now-datetime.timedelta(minutes=1)])

	    announce_interval = max(num_peers * announce_rate / (MAX_ANNOUNCE_RATE**2) * 60, MIN_ANNOUNCE_INTERVAL)
	    # calculate expiration time offset
	    if event == 'stopped':
	        expire_time = 0
	    else:
	        expire_time = announce_interval * EXPIRE_FACTOR

	    for p in peers:
	        if p['peer_id'] == args['peer_id']:
	            peers.remove(p)
	    if event == 'completed':
	        topic = Topic.objects.filter(torrent__pk=torrent_id)
	        if len(topic)>0:
	            topic[0].attrs['downloaded'] = topic[0].attrs.get('downloaded', 0)+1
	            topic[0].save()
	    if event != 'stopped':
	        peer_dict = {
	            'info_hash': info_hash,
	            'peer_id': args['peer_id'],
	            'ip': args['ip'],
	            'port': args['port'],
	            'uploaded': args['uploaded'],
	            'downloaded': args['downloaded'],
	            'left': args['left'],
	            'expire_time': now+datetime.timedelta(seconds=int(expire_time)),
	            'update_time': now,
	            'torrent_id': torrent_id,
	        }
	        if not OPEN_TRACKER:
	            peer_dict['user_id'] = u.id
	        peers.append(peer_dict)

	    mc.set('peers', peers)

	    numwant = request.GET.get('numwant', 50)
	    try:
	        numwant = int(numwant)
	    except ValueError:
	        numwant = 50
	    result = [p for p in peers if p['torrent_id'] == torrent_id and p['expire_time']>now and p['info_hash']==info_hash] #this may be optimized
	    shuffle(result)
	    result = result[:numwant]

	    if request.GET.get('compact'):
	        peers = ""
	        for peer in result:
	            peers += pack('>4sH', inet_aton(peer['ip']), peer['port'])
	    elif request.GET.get('no_peer_id'):
	        peers = []
	        for peer in result:
	            peers.append({'ip': peer['ip'], 'port': peer['port']})
	    else:
	        peers = []
	        for peer in result:
	            peers.append({'ip': peer['ip'], 'port': peer['port'], 'peer id': peer['peer_id']})

	    return HttpResponse(bencode({
	            'interval': int(announce_interval),
	            'peers': peers,
	        }),
	        mimetype = 'text/plain')

	except:
		response_fail(sys.exc_info()[0])


def scrape(request):
    #r = redis.StrictRedis(host='localhost')
    raise Exception(request.GET)
    return render_to_response('announce/scrape.html', {})


def response_fail(reason, xhr=False):
    if not xhr:
        return HttpResponse(benc.bencode({'failure reason': reason}))

    r = HttpResponse(mimetype="text/xml")
    r.write("""<?xml version="1.0" encoding="UTF-8"?>""")
    r.write("""<result><msg>failure</msg></result>""")
    return r
