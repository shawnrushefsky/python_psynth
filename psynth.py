__author__ = 'psymac0'
#coding=utf-8
import urllib
import simplejson as json
import uuid
import requests
from collections import deque


allowed_queries = ['createmap', 'getfilelist', 'renamemap', 'getwholegraph', 'newnode', 'batchnodes',
                    'delnode', 'newrel', 'batchrels', 'delrel', 'updatenode','updaterel', 'newdetail', 'deldetail',
                    'updatedetail', 'tag', 'newcomment', 'getcomments','setdrawparams', 'drawgraph', 'nodeplusone',
                    'interconnections', 'expandselection', 'setgraphname', 'getgraphname', 'sessionquit', 'saveprefs',
                    'getheat', 'newreltype', 'updatereltype', 'shortestpath', 'chatmessage', 'getchat', 'getqueue',
                    'getallpos', 'exporttoimage', 'publish']

class Graph:
    my_nodes = []
    my_node_index = {}
    my_links = []
    my_link_index = {}
    my_details = []
    my_detail_index = {}
    my_link_types = {}
    my_queries = deque()
    transit = False

    def __init__(self, name, filename, url, username, key):
        self.name = name
        self.filename = filename
        self.url = url
        self.username = username
        self.key = key

    def transmit(self):
        if len(self.my_queries) > 0:
            q = self.my_queries.popleft()
            c = requests.get(self.prep(q['query']), verify=False)
            if c.status_code == 200:
                cr = c.json()
                if q['callback']:
                    q['callback'](cr)
            elif c.status_code == 406:
                print q['query']+"    "+c.json()
            else:
                print q['query']+"    "+str(c.status_code)
            self.transmit()
        else:
            self.transit = False

    def queue(self, query, callback):
        self.my_queries.append({'query': query, 'callback': callback})
        if not self.transit:
            self.transit = True
            self.transmit()

    def id_tag(self, obj):
        obj['user'] = self.username
        obj['key'] = self.key
        if len(self.filename) > 0:
            obj['filename'] = self.filename
        return obj

    def prep(self, query):
        query = self.id_tag(query)
        if query['query'] not in allowed_queries:
            raise ValueError("'query' field contained an invalid value.")
        else:
            url = self.url+'api/'+json.dumps(query)
            return url

    def add_detail(self, detail, callback=None, update=True):
        if detail.__class__.__name__ == "Detail":
            detail.graph = self
            self.my_details.append(detail)
            self.my_detail_index[detail.uid] = detail
            if update:
                q = detail.dictionary()
                q['query'] = "newdetail"
                detail.created = True
                self.queue(q, callback)
        else:
            raise TypeError('Graph.add_detail requires a Detail-type object')

    def add_link(self, link, callback=None, update=True):
        if link.__class__.__name__ == "Link":
            link.graph = self
            self.my_links.append(link)
            self.my_link_index[link.uid] = link
            if update:
                q = link.dictionary()
                q['query'] = "newrel"
                link.created = True
                self.queue(q, callback)
        else:
            raise TypeError('Graph.add_link requires a Link-type object.')

    def add_link_type(self, link_type, callback=None, update=True):
        if link_type.__class__.__name__ == "LinkType":
            link_type.graph = self
            self.my_link_types[link_type.name] = link_type
            if update:
                q = link_type.dictionary()
                q['query'] = "newreltype"
                link_type.created = True
                self.queue(q, callback)
        else:
            raise TypeError('Graph.add_link_type requires a LinkType-type object.')

    def add_node(self, node, callback=None, update=True):
        if node.__class__.__name__ == "Node":
            node.graph = self
            self.my_nodes.append(node)
            self.my_node_index[node.uid] = node
            if update:
                q = node.dictionary()
                q['query'] = "newnode"
                node.created = True
                self.queue(q, callback)
        else:
            raise TypeError('Graph.add_node requires a Node-type object.')

    def detail(self, uid):
        if uid in self.my_detail_index:
            return self.my_detail_index[uid]

    def detail_list(self):
        return self.my_details

    def details(self):
        return self.my_detail_index

    def draw(self, callback=None):
        q = {'query': 'drawgraph'}

        def handler(r):
            for n in r['nodes']:
                self.my_node_index[n['UID']].x = n['X']
                self.my_node_index[n['UID']].y = n['Y']
            for d in r['details']:
                self.my_detail_index[d['UID']].x = d['X']
                self.my_detail_index[d['UID']].y = d['Y']
            if callback:
                callback(r)
        self.queue(q, handler)

    def height(self):
        return self.max_y()-self.min_y()

    def link(self, uid):
        if uid in self.my_link_index:
            return self.my_link_index[uid]

    def link_list(self):
        return self.my_links

    def links(self):
        return self.my_link_index

    def link_type(self, name):
        if name in self.my_link_types:
            return self.my_link_types[name]

    def link_types(self):
        return self.my_link_types

    def max_x(self):
        m = None
        for n in self.my_nodes:
            if not m or n.x > m:
                m = n.x
        return m

    def max_y(self):
        m = None
        for n in self.my_nodes:
            if not m or n.y > m:
                m = n.y
        return m

    def min_x(self):
        m = None
        for n in self.my_nodes:
            if not m or n.x < m:
                m = n.x
        return m

    def min_y(self):
        m = None
        for n in self.my_nodes:
            if not m or n.y < m:
                m = n.y
        return m

    def node(self, uid):
        if uid in self.my_node_index:
            return self.my_node_index[uid]

    def node_list(self):
        return self.my_nodes

    def nodes(self):
        return self.my_node_index

    def publish(self, callback=None):
        q = {'query': 'publish', 'x': -(self.min_x()+.1), 'y': -(self.min_y()+.1), 'scale': 1080/self.height()}

        def handler(r):
            print "Graph published at "+self.url+'p/ublic/'+urllib.unquote(r)
            if callback:
                callback(r)

        self.queue(q, handler)

    def remove_detail(self, detail, callback=None, update=True):
        self.my_details.remove(detail)
        del self.my_detail_index[detail.uid]
        if update:
            q = {'query': 'deldetail', 'uid': detail.uid}
            self.queue(q, callback)

    def remove_link(self, link, callback=None, update=True):
        self.my_links.remove(link)
        del self.my_link_index[link.uid]
        if update:
            q = {'query': 'delrel', 'uid': link.uid}
            self.queue(q, callback)

    def remove_node(self, node, callback=None, update=True):
        self.my_nodes.remove(node)
        del self.my_node_index[node.uid]
        if update:
            q = {'query': 'delnode', 'uid': node.uid}
            self.queue(q, callback)

    def width(self):
        return self.max_x()-self.min_x()


class Node():
    def __init__(self, uid=None, name="New Node", x=1, y=1, shape=6, image="na", radius=24, color="default"):
        if not uid:
            uid = str(uuid.uuid4())
        self.name = urllib.unquote(name)
        self.uid = urllib.unquote(uid)
        self.x = float(x)
        self.y = float(y)
        self.shape = int(shape)
        self.image = urllib.unquote(image)
        self.radius = radius
        self.color = urllib.unquote(color)
        self.created = False

    graph = None

    def add_detail(self, detail, update=True, callback=None):
        detail.anchor_type = self.__class__.__name__
        detail.anchor_uid = self.uid
        if not detail.x:
            detail.x = self.x+self.radius+4
        if not detail.y:
            num = 0
            for d in self.graph.detail_list():
                if d.anchor_uid == self.uid:
                    num += 1
            detail.y = self.y+self.radius+(20*num)
        self.graph.add_detail(detail, update=update, callback=callback)

    def details(self):
        dets = {}
        for d in self.graph.detail_list():
            if d.anchor_uid == self.uid:
                dets[d.uid] = d
        return dets

    def detail_list(self):
        dets = []
        for d in self.graph.detail_list():
            if d.anchor_uid == self.uid:
                dets.append = d
        return dets

    def out_links(self):
        links = []
        for l in self.graph.link_list():
            if l.origin_uid == self.uid:
                links.append(l)
        return links

    def in_links(self):
        links = []
        for l in self.graph.link_list():
            if l.terminus_uid == self.uid:
                links.append(l)
        return links

    def all_links(self):
        links = []
        for l in self.graph.link_list():
            if l.origin_uid == self.uid or l.terminus_uid == self.uid:
                links.append(l)
        return links

    def out_neighbors(self):
        neighbors = []
        for l in self.graph.link_list():
            if l.origin_uid == self.uid:
                neighbors.append(l.terminus())
        return neighbors

    def in_neighbors(self):
        neighbors = []
        for l in self.graph.link_list():
            if l.terminus_uid == self.uid:
                neighbors.append(l.origin())
        return neighbors

    def all_neighbors(self):
        neighbors = []
        for l in self.graph.link_list():
            if l.terminus_uid == self.uid:
                neighbors.append(l.origin())
            elif l.origin_uid == self.uid:
                neighbors.append(l.terminus())
        return neighbors

    def dictionary(self):
        return {'uid': urllib.quote(self.uid),
                'name': urllib.quote(self.name),
                'x': str(self.x),
                'y': str(self.y),
                'radius': self.radius,
                'shape': str(self.shape),
                'picture': urllib.quote(self.image),
                'color': urllib.quote(self.color)}

    def update(self, callback=None):
        q = self.dictionary()
        q['query'] = "updatenode"
        self.graph.queue(q, callback)


class Link():
    def __init__(self, origin_uid, terminus_uid, type, name="Link", value=1, uid=None):
        if not uid:
            uid = str(uuid.uuid4())
        self.origin_uid = urllib.unquote(origin_uid)
        self.terminus_uid = urllib.unquote(terminus_uid)
        self.type = urllib.unquote(type)
        self.name = urllib.unquote(name)
        self.value = int(value)
        self.uid = urllib.unquote(uid)
        self.created = False

    graph = None

    def add_detail(self, detail, update=True, callback=None):
        detail.anchor_type = self.__class__.__name__
        detail.anchor_uid = self.uid
        if not detail.x:
            raise TypeError("Detail.x is not defined.")
        if not detail.y:
            raise TypeError("Detail.y is not defined.")
        self.graph.add_detail(detail, update=update, callback=callback)

    def detail_list(self):
        dets = []
        for d in self.graph.detail_list():
            if d.anchor_uid == self.uid:
                dets.append(d)
        return dets

    def details(self):
        dets = {}
        for d in self.graph.detail_list():
            if d.anchor_uid == self.uid:
                dets[d.uid] = d
        return dets

    def dictionary(self):
        return {'uid': urllib.quote(self.uid),
                'name': urllib.quote(self.name),
                'value': str(self.value),
                'rel_type': urllib.quote(self.type),
                'o_uid': urllib.quote(self.origin_uid),
                't_uid': urllib.quote(self.terminus_uid)}

    def origin(self):
        return self.graph.node(self.origin_uid)

    def parallel(self):
        ps = []
        for l in self.graph.link_list():
            if l.origin_uid == self.origin_uid and l.terminus_uid == self.terminus_uid:
                ps.append(l)
            elif l.origin_uid == self.terminus_uid and l.terminus_uid == self.origin_uid:
                ps.append(l)
        return ps

    def terminus(self):
        return self.graph.node(self.terminus_uid)

    def update(self, callback=None):
        q = self.dictionary()
        q['query'] = "updaterel"
        self.graph.queue(q, callback)


class LinkType:
    def __init__(self, name='Links', icon='img/link_icon.png', tile='img/link_tile.png', color='#1AA2D4', max=10):
        self.name = urllib.unquote(name)
        self.icon = urllib.unquote_plus(icon)
        self.tile = urllib.unquote_plus(tile)
        self.color = urllib.unquote(color)
        self.max = int(max)
        self.created = False

    graph = None

    def dictionary(self):
        return {'NAME': urllib.quote(self.name),
                'ICON': urllib.quote_plus(self.icon),
                'TILE': urllib.quote_plus(self.tile),
                'COLOR': urllib.quote(self.color),
                'MAX': self.max}

    def update(self, callback=None):
        q = self.dictionary()
        q['query'] = "updatereltype"
        self.graph.queue(q, callback)


class Detail:
    def __init__(self, content, anchor_uid=None, anchor_type=None, x=None, y=None, type='comment', name=None, uid=None):
        if not uid:
            uid = str(uuid.uuid4())
        if anchor_uid:
            self.anchor_uid = urllib.unquote(anchor_uid)
        else:
            self.anchor_uid = anchor_uid
        if anchor_type:
            self.anchor_type = anchor_type
        else:
            self.anchor_type = anchor_type
        self.content = urllib.unquote(content)
        if x:
            self.x = float(x)
        else:
            self.x = x
        if y:
            self.y = float(y)
        else:
            self.y = y
        self.type = type
        self.name = urllib.unquote(name)
        self.uid = urllib.unquote(uid)
        self.created = False

    graph = None

    def anchor(self):
        if self.anchor_type == "Node":
            return self.graph.node(self.anchor_uid)
        elif self.anchor_type == "Link":
            return self.graph.link(self.anchor_uid)

    def dictionary(self):
        return {'anchor_uid': urllib.quote(self.anchor_uid),
                'anchor_type': self.anchor_type,
                'uid': urllib.quote(self.uid),
                'name': urllib.quote(self.name),
                'content': urllib.quote(self.content),
                'type': self.type,
                'x': str(self.x),
                'y': str(self.y)}

    def update(self, callback=None):
        q = self.dictionary()
        q['query'] = "updatedetail"
        self.graph.queue(q, callback)


def create_graph(name, url, username, key):
    g = Graph(name=name,
              url=url,
              username=username,
              key=key,
              filename='')
    c = requests.get(g.prep({'query': 'createmap',
                             'name': 'Insurgents 1776'}), verify=False)
    if c.status_code == 200:
        cr = c.json()
        print cr
        g.filename = cr['filename']
        return g
    elif c.status_code == 406:
        print c.url+"    "+c.json()
    else:
        print c.url+"    "+str(c.status_code)


def load_graph(filename, url, username, key):
    g = Graph(name='',
              url=url,
              username=username,
              key=key,
              filename=filename)
    c = requests.get(g.prep({'query': 'getwholegraph'}), verify=False)
    if c.status_code == 200:
        cr = c.json()
        g.name = cr['name']
        lts = cr['rel_types']
        ns = cr['nodes']
        ls = cr['rels']
        ds = cr['details']
        for t in lts:
            lt = LinkType(name=t['NAME'],
                          icon=t['ICON'],
                          tile=t['TILE'],
                          color=t['COLOR'],
                          max=t['MAX'])
            lt.created = True
            g.add_link_type(lt, update=False)
        for n in ns:
            nn = Node(uid=n['UID'],
                      name=n['NAME'],
                      x=n['X'],
                      y=n['Y'],
                      shape=n['SHAPE'],
                      radius=n['RADIUS'],
                      color=n['COLOR'],
                      image=n['PICTURE'])
            nn.created = True
            g.add_node(nn, update=False)
        for l in ls:
            ll = Link(name=l['NAME'],
                      type=l['TYPE'],
                      value=l['VALUE'],
                      origin_uid=l['ORIGIN'],
                      terminus_uid=l['TERMINUS'],
                      uid=l['UID'])
            ll.created = True
            g.add_link(ll, update=False)
        for d in ds:
            dd = Detail(anchor_type=d['ANCHOR_TYPE'],
                        anchor_uid=d['ANCHOR_UID'],
                        name=d['NAME'],
                        type=d['TYPE'],
                        content=d['CONTENT'],
                        uid=d['UID'],
                        x=d['X'],
                        y=d['Y'])
            dd.created = True
            g.add_detail(dd, update=False)
        return g
    elif c.status_code == 406:
        print c.url+"    "+c.json()
    else:
        print c.url+"    "+str(c.status_code)