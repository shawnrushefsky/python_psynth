__author__ = 'psymac0'
#coding=utf-8
import urllib
import simplejson as json
import uuid
import requests
from collections import deque
## @package pyPsynth
#  pyPsynth is the official python package for generating graphs in Psymphonic Psynth

allowed_queries = ['createmap', 'getfilelist', 'renamemap', 'getwholegraph', 'newnode', 'batchnodes',
                    'delnode', 'newrel', 'batchrels', 'delrel', 'updatenode','updaterel', 'newdetail', 'deldetail',
                    'updatedetail', 'tag', 'newcomment', 'getcomments','setdrawparams', 'drawgraph', 'nodeplusone',
                    'interconnections', 'expandselection', 'setgraphname', 'getgraphname', 'sessionquit', 'saveprefs',
                    'getheat', 'newreltype', 'updatereltype', 'shortestpath', 'chatmessage', 'getchat', 'getqueue',
                    'getallpos', 'exporttoimage', 'publish']
##
# The Graph is a structured collection of Node, Link, LinkType, and Detail objects.
# Most actions are performed through the Graph class.
#
class Graph:
    __nodes = []
    __node_index = {}
    __links = []
    __link_index = {}
    __details = []
    __details_index = {}
    __link_types = {}
    __queries = deque()
    __transit = False

    def __init__(self, name, filename, url, username, key):
        ##
        # This is the constructor for the Graph class. It should not be accessed directly,
        # but instead through the pyPsynth.create_graph and pyPsynth.load_graph functions.
        # @param name: <i>str</i> The displayed name of a Graph.
        # @param filename: <i>str</i> A global unique filename of a Graph.
        # @param url: <i>str</i> The base URL of your Psynth server. e.g. https://psynth.psymphonic.com/
        # @param username: <i>str</i> Your Psynth username
        # @param key: <i>str</i> Your Psynth API key.
        #
        # @code
        # g = pyPsynth.load_graph(
        #     filename='myfile.gt',
        #     url='https://psynth.psymphonic.com/',
        #     username='me@company.com',
        #     key='myapikey'
        # )
        # @endcode
        #
        # @code
        # g = pyPsynth.create_graph(
        #     name='my graph',
        #     url='https://psynth.psymphonic.com/',
        #     username='me@company.com',
        #     key='myapikey'
        # )
        # @endcode
        self.name = name
        self.filename = filename
        self.url = url
        self.username = username
        self.key = key

    def __transmit(self):
        if len(self.__queries) > 0:
            q = self.__queries.popleft()
            c = requests.get(self.prep(q['query']), verify=False)
            if c.status_code == 200:
                cr = c.json()
                if q['callback']:
                    q['callback'](cr)
            elif c.status_code == 406:
                print q['query']+"    "+c.json()
            else:
                print q['query']+"    "+str(c.status_code)
            self.__transmit()
        else:
            self.__transit = False

    def queue(self, query, callback):
        ##
        # All queries should be processed through this function to ensure that they process in order.
        # Mostly used internally.
        #
        # @param query: <i>dict</i> A dictionary object that contains query parameters.
        # @param callback: <i>function</i> A function that should be performed on the response from the query.
        #
        # @code
        # def point_handler(r):
        #     print r
        # g.queue({'query': 'drawgraph'}, point_handler)
        # @endcode
        self.__queries.append({'query': query, 'callback': callback})
        if not self.__transit:
            self.__transit = True
            self.__transmit()

    def __id_tag(self, obj):
        ##
        # This attaches the 'username', 'key', and 'filename' fields to the query dictionary.
        # Mostly for internal use.
        #
        # @param obj: <i>dict</i> The query to tag up.
        # @return obj: <i>dict</i> The updated query dictionary.
        # #
        obj['user'] = self.username
        obj['key'] = self.key
        if len(self.filename) > 0:
            obj['filename'] = self.filename
        return obj

    def prep(self, query):
        ##
        # Turns a query dictionary into a valid URL. Mostly used internally.
        #
        # @param query: <i>dict</i> A query dictionary.
        # @return url: <i>str</i> A valid URL
        #
        query = self.__id_tag(query)
        if query['query'] not in allowed_queries:
            raise ValueError("'query' field contained an invalid value.")
        else:
            url = self.url+'api/'+json.dumps(query)
            return url

    def add_detail(self, detail, callback=None, update=True):
        ##
        # This adds a Detail to the Graph. It is easier to add Detail objects directly to Node and Link objects.
        #
        # @param detail: <i>Detail</i> A Detail object to add to the Graph.
        # @param callback: <i>function</i> A function to perform on the response of the query.
        # @param update: <i>bool</i> Whether or not to immediately enqueue the query.
        #
        if detail.__class__.__name__ == "Detail":
            detail.graph = self
            self.__details.append(detail)
            self.__details_index[detail.uid] = detail
            if update:
                q = detail.dictionary()
                q['query'] = "newdetail"
                detail.created = True
                self.queue(q, callback)
        else:
            raise TypeError('Graph.add_detail requires a Detail-type object')

    def add_link(self, link, callback=None, update=True):
        ##
        # This adds a Link to the Graph.
        #
        # @param link: <i>Link</i> A Link to add to the Graph.
        # @param callback: <i>function</i> A function to perform on the response to the query.
        # @param update: <i>bool</i> Whether or not to immediately enqueue the query.
        #
        if link.__class__.__name__ == "Link":
            link.graph = self
            self.__links.append(link)
            self.__link_index[link.uid] = link
            if update:
                q = link.dictionary()
                q['query'] = "newrel"
                link.created = True
                self.queue(q, callback)
        else:
            raise TypeError('Graph.add_link requires a Link-type object.')

    def add_link_type(self, link_type, callback=None, update=True):
        ##
        # Adds a LinkType to the Graph. Must be added before Link objects of that type can be created.
        #
        # @param link_type: <i>LinkType</i> A LinkType to add to the Graph
        # @param callback: <i>function</i> A function to perform on the response to the query.
        # @param update: <i>bool</i> Whether or not to immediately enqueue the query.
        #
        if link_type.__class__.__name__ == "LinkType":
            link_type.graph = self
            self.__link_types[link_type.name] = link_type
            if update:
                q = link_type.dictionary()
                q['query'] = "newreltype"
                link_type.created = True
                self.queue(q, callback)
        else:
            raise TypeError('Graph.add_link_type requires a LinkType-type object.')

    def add_node(self, node, callback=None, update=True):
        ##
        # Adds a Node to the Graph.
        #
        # @param node: <i>Node</i> The Node to add to the Graph.
        # @param callback: <i>function</i> A function to perform on the response from the server.
        # @param update: Whether or not to immediately enqueue the query.
        #
        if node.__class__.__name__ == "Node":
            node.graph = self
            self.__nodes.append(node)
            self.__node_index[node.uid] = node
            if update:
                q = node.dictionary()
                q['query'] = "newnode"
                node.created = True
                self.queue(q, callback)
        else:
            raise TypeError('Graph.add_node requires a Node-type object.')

    def detail(self, uid):
        ##
        # Returns a Detail by its UID
        #
        # @param uid: <i>str</i> The uid of the Detail to return.
        # @return detail: <i>Detail</i>
        #
        if uid in self.__details_index:
            return self.__details_index[uid]
        return None

    def detail_list(self):
        ##
        # Returns a list of Detail objects in the Graph.
        #
        # @return details: <i>list</i> A list of Detail objects.
        #
        return self.__details

    def details(self):
        ##
        # Returns a dictionary of Detail objects keyed by uid.
        #
        # @return details: <i>dict</i> A uid-indexed dictionary of Detail objects.
        #
        return self.__details_index

    def draw(self, callback=None):
        ##
        # Calculates a layout for the Graph and returns new positions for all Node and Detail objects.
        #
        # @param callback: <i>function</i> A function to perform on the response from the server.
        #
        q = {'query': 'drawgraph'}

        def handler(r):
            for n in r['nodes']:
                self.__node_index[n['UID']].x = n['X']
                self.__node_index[n['UID']].y = n['Y']
            for d in r['details']:
                self.__details_index[d['UID']].x = d['X']
                self.__details_index[d['UID']].y = d['Y']
            if callback:
                callback(r)
        self.queue(q, handler)

    def height(self):
        ##
        # Returns the height of the Graph.
        #
        # @return height: <i>float</i>
        #
        return self.max_y()-self.min_y()

    def link(self, uid):
        ##
        # Returns a Link by uid.
        #
        # @param uid: <i>str</i> The uid of the Link to return.
        # @return link: <i>Link</i>
        #
        if uid in self.__link_index:
            return self.__link_index[uid]
        else:
            return None

    def link_list(self):
        ##
        # Returns a list of Link objects in the Graph.
        #
        # @return links: <i>list</i> A list of Link objects.
        #
        return self.__links

    def links(self):
        ##
        # Returns a uid-keyed dictionary of Link objects in the Graph.
        #
        # @return links: <i>dict</i> A uid-keyed dictionary of Link objects.
        #
        return self.__link_index

    def link_type(self, name):
        ##
        # Returns a LinkType object by name.
        #
        # @param name: <i>str</i> The name of the LinkType to return.
        # @return link_type: <i>LinkType</i>
        #
        if name in self.__link_types:
            return self.__link_types[name]

    def link_types(self):
        ##
        # Returns a name-indexed dictionary of LinkType objects.
        #
        # @return link_types: <i>dict</i> A name-indexed dictionary of LinkType objects.
        #
        return self.__link_types

    def max_x(self):
        ##
        # Returns the maximum x value of all Node objects in the Graph.
        #
        # @return x: <i>float</i>
        #
        m = None
        for n in self.__nodes:
            if not m or n.x > m:
                m = n.x
        return m

    def max_y(self):
        ##
        # Returns the maximum y value of all Node objects in the Graph.
        #
        # @return y: <i>float</i>
        #
        m = None
        for n in self.__nodes:
            if not m or n.y > m:
                m = n.y
        return m

    def min_x(self):
        ##
        # Returns the minimum x value of all Node objects in the Graph.
        #
        # @return x: <i>float</i>
        #
        m = None
        for n in self.__nodes:
            if not m or n.x < m:
                m = n.x
        return m

    def min_y(self):
        ##
        # Returns the minimum y value of all Node objects in the Graph.
        #
        # @return y: <i>float</i>
        #
        m = None
        for n in self.__nodes:
            if not m or n.y < m:
                m = n.y
        return m

    def node(self, uid):
        ##
        # Returns a Node by uid.
        #
        # @param uid: <i>str</i> The uid of the Node to be returned.
        # @return node: <i>Node</i>
        #
        if uid in self.__node_index:
            return self.__node_index[uid]
        else:
            return None

    def node_list(self):
        ##
        # Returns a list of all Node objects in the Graph.
        #
        # @return nodes: <i>list</i> A list of Node objects.
        #
        return self.__nodes

    def nodes(self):
        ##
        # Returns a uid-indexed dictionary of Node objects.
        #
        # @return nodes: <i>dict</i> A uid-indexed dictionary of Node objects.
        #
        return self.__node_index

    def publish(self, callback=None):
        ##
        # Creates a perma-link for a public viewer of the graph.
        #
        # @param callback: <i>function</i> A function to perform on the response from the query.
        #
        q = {'query': 'publish', 'x': -(self.min_x()+.1), 'y': -(self.min_y()+.1), 'scale': 1080/self.height()}

        def handler(r):
            print "Graph published at "+self.url+'p/ublic/'+urllib.unquote(r)
            if callback:
                callback(r)

        self.queue(q, handler)

    def remove_detail(self, detail, callback=None, update=True):
        ##
        # Removes a Detail from the Graph.
        #
        # @param detail: <i>Detail</i> The Detail to remove.
        # @param callback: <i>function</i> A function to perform on the response from the query.
        # @param update: <i>bool</i> Whether or not to immediately enqueue the query.
        #
        self.__details.remove(detail)
        del self.__details_index[detail.uid]
        if update:
            q = {'query': 'deldetail', 'uid': detail.uid}
            self.queue(q, callback)

    def remove_link(self, link, callback=None, update=True):
        ##
        # Removes a Link from the Graph.
        #
        # @param link: <i>Link<i> The Link to remove.
        # @param callback: <i>function<i> A function to perform on the response from the query.
        # @param update: <i>bool</i> Whether or not to immediately enqueue the query.
        #
        self.__links.remove(link)
        del self.__link_index[link.uid]
        if update:
            q = {'query': 'delrel', 'uid': link.uid}
            self.queue(q, callback)

    def remove_node(self, node, callback=None, update=True):
        ##
        # Removes a Node from the Graph.
        #
        # @param node: <i>Node</i> The Node to remove.
        # @param callback: <i>function<i> A function to perform on the response from the query.
        # @param update: <i>bool</i> Whether or not to immediately enqueue the query.
        self.__nodes.remove(node)
        del self.__node_index[node.uid]
        if update:
            q = {'query': 'delnode', 'uid': node.uid}
            self.queue(q, callback)

    def width(self):
        ##
        # Returns the width of the Graph.
        #
        # @return width: <i>float</i>
        #
        return self.max_x()-self.min_x()

##
# Nodes are the basic unit in Psynth. They can be connected by Link objects, and Detail objects can be attached to them.
#
class Node():
    def __init__(self, uid=None, name="New Node", x=1, y=1, shape=6, image="na", radius=24, color="default"):
        ##
        #
        # @param uid:
        # @param name:
        # @param x:
        # @param y:
        # @param shape:
        # @param image:
        # @param radius:
        # @param color:
        #
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
            for d in self.graph.detail_list:
                if d.anchor_uid == self.uid:
                    num += 1
            detail.y = self.y+self.radius+(20*num)
        self.graph.add_detail(detail, update=update, callback=callback)

    def details(self):
        dets = {}
        for d in self.graph.detail_list:
            if d.anchor_uid == self.uid:
                dets[d.uid] = d
        return dets

    def detail_list(self):
        dets = []
        for d in self.graph.detail_list:
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

##
# Links connect Node objects to each other. They have a LinkType.  Detail objects can be attached to them.
#
class Link():
    def __init__(self, origin_uid, terminus_uid, type, name="Link", value=1, uid=None):
        ##
        #
        # @param origin_uid:
        # @param terminus_uid:
        # @param type:
        # @param name:
        # @param value:
        # @param uid:
        #
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

    def link_type(self):
        return self.graph.link_type(self.type)

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
        for d in self.graph.detail_list:
            if d.anchor_uid == self.uid:
                dets.append(d)
        return dets

    def details(self):
        dets = {}
        for d in self.graph.detail_list:
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

##
# LinkType objects define the parameters of Link objects.
#
class LinkType:
    def __init__(self, name='Links', icon='img/link_icon.png', tile='img/link_tile.png', color='#1AA2D4', max=10):
        ##
        #
        # @param name:
        # @param icon:
        # @param tile:
        # @param color:
        # @param max:
        #
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

##
# Detail objects contain links or text, and can be attached to Node objects and Link objects.
#
class Detail:
    def __init__(self, content, anchor_uid=None, anchor_type=None, x=None, y=None, type='comment', name=None, uid=None):
        ##
        #
        # @param content:
        # @param anchor_uid:
        # @param anchor_type:
        # @param x:
        # @param y:
        # @param type:
        # @param name:
        # @param uid:
        #
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