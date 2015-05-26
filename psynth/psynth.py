__author__ = 'psymphonic'
#coding=utf-8
import urllib
import simplejson as json
import uuid
import requests
from collections import deque
## @package psynth
#  psynth is the official python package for generating graphs in Psymphonic Psynth

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
        # but instead through the create_graph and load_graph functions.
        # @param name: <i>str</i> :: The displayed name of a Graph.
        # @param filename: <i>str</i> :: A global unique filename of a Graph.
        # @param url: <i>str</i> :: The base URL of your Psynth server. e.g. https://psynth.psymphonic.com/
        # @param username: <i>str</i> :: Your Psynth username
        # @param key: <i>str</i> :: Your Psynth API key.
        #
        # @code
        # g = load_graph(
        #     filename='myfile.gt',
        #     url='https://psynth.psymphonic.com/',
        #     username='me@company.com',
        #     key='myapikey'
        # )
        # @endcode
        #
        # @code
        # g = create_graph(
        #     name='my graph',
        #     url='https://psynth.psymphonic.com/',
        #     username='me@company.com',
        #     key='myapikey'
        # )
        # @endcode

        ## <i>str</i> :: The display name of the Graph.
        self.name = name

        ## <i>str</i> :: The global unique filename of the Graph.
        self.filename = filename

        ## <i>str</i> :: The base URL for your psynth server. e.g. "https://psynth.psymphonic.com/"
        self.url = url

        ## <i>str</i> :: Your Psynth username.
        self.username = username

        ## <i>str</i> :: Your Psynth API Key.
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
                raise SyntaxError(str(q['query'])+"    "+c.json())
            else:
                raise SyntaxError(str(q['query'])+"    "+str(c.status_code))
            self.__transmit()
        else:
            self.__transit = False

    def queue(self, query, callback):
        ##
        # All queries should be processed through this function to ensure that they process in order.
        # Mostly used internally.
        #
        # @param query: <i>dict</i> :: A dictionary object that contains query parameters.
        # @param callback: <i>function</i> :: A function that should be performed on the response from the query.
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
        # @param obj: <i>dict</i> :: The query to tag up.
        # @return obj: <i>dict</i> :: The updated query dictionary.
        #
        obj['user'] = self.username
        obj['key'] = self.key
        if len(self.filename) > 0:
            obj['filename'] = self.filename
        return obj

    def prep(self, query):
        ##
        # Turns a query dictionary into a valid URL. Mostly used internally.
        #
        # @param query: <i>dict</i> :: A query dictionary.
        # @return url: <i>str</i> :: A valid URL
        #
        # @code
        # c = requests.get(g.prep(query))
        # print c.json()
        # @endcode
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
        # @param detail: <i>Detail</i> :: A Detail object to add to the Graph.
        # @param callback: <i>function</i> :: A function to perform on the response of the query.
        # @param update: <i>bool</i> :: Whether or not to immediately enqueue the query.
        #
        # @code
        # g.add_detail(my_detail, callback=my_function)
        # @endcode
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
        # @param link: <i>Link</i> :: A Link to add to the Graph.
        # @param callback: <i>function</i> :: A function to perform on the response to the query.
        # @param update: <i>bool</i> :: Whether or not to immediately enqueue the query.
        #
        # @code
        # g.add_link(my_link, callback=my_function)
        # @endcode
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
        # @param link_type: <i>LinkType</i> :: A LinkType to add to the Graph
        # @param callback: <i>function</i> :: A function to perform on the response to the query.
        # @param update: <i>bool</i> :: Whether or not to immediately enqueue the query.
        #
        # @code
        # g.add_link_type(my_link_type, callback=my_function)
        # @endcode
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
        # @param node: <i>Node</i> :: The Node to add to the Graph.
        # @param callback: <i>function</i> :: An optional function to handle the server's response to the query.
        # @param update: Whether or not to immediately enqueue the query.
        #
        # @code
        # g.add_node(my_node, callback=my_function)
        # @endcode
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
        # @param uid: <i>str</i> :: The uid of the Detail to return.
        # @return detail: <i>Detail</i> ::
        #
        # @code
        # my_detail = g.detail(unique_id)
        # @endcode
        if uid in self.__details_index:
            return self.__details_index[uid]
        return None

    def detail_list(self):
        ##
        # Returns a list of Detail objects in the Graph.
        #
        # @return details: <i>list</i> :: A list of Detail objects.
        #
        # @code
        # for d in g.detail_list():
        #     print d.content
        # @endcode
        return self.__details

    def details(self):
        ##
        # Returns a dictionary of Detail objects keyed by uid.
        #
        # @return details: <i>dict</i> :: A uid-keyed dictionary of Detail objects.
        #
        # @code
        # for d in g.details():
        #     print g.details()[d].anchor().name
        # @endcode
        return self.__details_index

    def draw(self, callback=None):
        ##
        # Calculates a layout for the Graph and returns new positions for all Node and Detail objects.
        #
        # @param callback: <i>function</i> :: An optional function to handle the server's response to the query.
        #
        # @code
        # for i in range(0, 100):
        #     n = Node(name='Node '+str(i))
        #     g.add_node(n)
        # g.draw()
        # @endcode
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
        # @return height: <i>float</i> ::
        #
        # @code
        # h = g.height()
        # @endcode
        return self.max_y()-self.min_y()

    def link(self, uid):
        ##
        # Returns a Link by uid.
        #
        # @param uid: <i>str</i> :: The uid of the Link to return.
        # @return link: <i>Link</i> ::
        #
        # @code
        # my_link = g.link(unique_id)
        # @endcode
        if uid in self.__link_index:
            return self.__link_index[uid]
        else:
            return None

    def link_list(self):
        ##
        # Returns a list of Link objects in the Graph.
        #
        # @return links: <i>list</i> :: A list of Link objects.
        #
        # @code
        # for link in g.link_list():
        #     print link.name
        # @endcode
        return self.__links

    def links(self):
        ##
        # Returns a uid-keyed dictionary of Link objects in the Graph.
        #
        # @return links: <i>dict</i> :: A uid-keyed dictionary of Link objects.
        #
        # @code
        # for uid in g.links():
        #     print g.links()[uid].name
        # @endcode
        return self.__link_index

    def link_type(self, name):
        ##
        # Returns a LinkType object by name.
        #
        # @param name: <i>str</i> :: The name of the LinkType to return.
        # @return link_type: <i>LinkType</i> ::
        #
        # @code
        # lt = g.link_type('Money')
        # @endcode
        if name in self.__link_types:
            return self.__link_types[name]

    def link_types(self):
        ##
        # Returns a name-keyed dictionary of LinkType objects.
        #
        # @return link_types: <i>dict</i> :: A name-keyed dictionary of LinkType objects.
        #
        # @code
        # for lt in g.link_types():
        #     print len(g.link_types[lt].links())
        # @endcode
        return self.__link_types

    def max_x(self):
        ##
        # Returns the maximum x value of all Node objects in the Graph.
        #
        # @return x: <i>float</i> ::
        #
        # @code
        # n = Node(x=g.max_x()+50)
        # g.add_node(n)
        # @endcode
        m = None
        for n in self.__nodes:
            if not m or n.x > m:
                m = n.x
        return m

    def max_y(self):
        ##
        # Returns the maximum y value of all Node objects in the Graph.
        #
        # @return y: <i>float</i> ::
        #
        # @code
        # n = Node(y=g.max_y()-50)
        # g.add_node(n)
        # @endcode
        m = None
        for n in self.__nodes:
            if not m or n.y > m:
                m = n.y
        return m

    def min_x(self):
        ##
        # Returns the minimum x value of all Node objects in the Graph.
        #
        # @return x: <i>float</i> ::
        #
        # @code
        # n = Node(x=g.min_x()+50)
        # g.add_node(n)
        # @endcode
        m = None
        for n in self.__nodes:
            if not m or n.x < m:
                m = n.x
        return m

    def min_y(self):
        ##
        # Returns the minimum y value of all Node objects in the Graph.
        #
        # @return y: <i>float</i> ::
        #
        # @code
        # n = Node(x=g.min_y()+50)
        # g.add_node(n)
        # @endcode
        m = None
        for n in self.__nodes:
            if not m or n.y < m:
                m = n.y
        return m

    def node(self, uid):
        ##
        # Returns a Node by uid.
        #
        # @param uid: <i>str</i> :: The uid of the Node to be returned.
        # @return node: <i>Node</i> ::
        #
        # @code
        # n = g.node(unique_id)
        # @endcode
        if uid in self.__node_index:
            return self.__node_index[uid]
        else:
            return None

    def node_list(self):
        ##
        # Returns a list of all Node objects in the Graph.
        #
        # @return nodes: <i>list</i> :: A list of Node objects.
        #
        # @code
        # for n in g.node_list():
        #     print n.name
        # @endcode
        return self.__nodes

    def nodes(self):
        ##
        # Returns a uid-keyed dictionary of Node objects.
        #
        # @return nodes: <i>dict</i> :: A uid-keyed dictionary of Node objects.
        #
        # @code
        # for n in g.nodes():
        #     print g.nodes()[n].name
        # @endcode
        return self.__node_index

    def publish(self, callback=None):
        ##
        # Creates a perma-link for a public viewer of the graph.
        #
        # @param callback: <i>function</i> :: An optional function to handle the server's response to the query.
        #
        # @code
        # g.draw()
        # g.publish()
        # @endcode
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
        # @param detail: <i>Detail</i> :: The Detail to remove.
        # @param callback: <i>function</i> :: An optional function to handle the server's response to the query.
        # @param update: <i>bool</i> :: Whether or not to immediately enqueue the query.
        #
        # @code
        # g.remove_detail(my_detail, callback=my_function)
        # @endcode
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
        # @param callback: <i>function</i> :: An optional function to handle the server's response to the query.
        # @param update: <i>bool</i> :: Whether or not to immediately enqueue the query.
        #
        # @code
        # g.remove_link(my_link, callback=my_function)
        # @endcode
        self.__links.remove(link)
        del self.__link_index[link.uid]
        if update:
            q = {'query': 'delrel', 'uid': link.uid}
            self.queue(q, callback)

    def remove_node(self, node, callback=None, update=True):
        ##
        # Removes a Node from the Graph.
        #
        # @param node: <i>Node</i> :: The Node to remove.
        # @param callback: <i>function</i> :: An optional function to handle the server's response to the query.
        # @param update: <i>bool</i> :: Whether or not to immediately enqueue the query.
        #
        # @code
        # g.remove_node(my_node, callback=my_function)
        # @endcode
        self.__nodes.remove(node)
        del self.__node_index[node.uid]
        if update:
            q = {'query': 'delnode', 'uid': node.uid}
            self.queue(q, callback)

    def width(self):
        ##
        # Returns the width of the Graph.
        #
        # @return width: <i>float</i> ::
        #
        # @code
        # print g.width()
        # @endcode
        return self.max_x()-self.min_x()

##
# Nodes are the basic unit in Psynth. They can be connected by Link objects, and Detail objects can be attached to them.
#
class Node():
    def __init__(self, uid=None, name="New Node", x=1.0, y=1.0, shape=6, image="na", radius=24.0, color="dynamic"):
        ##
        # Constructs a Node object.
        #
        # @param uid: <i>str</i> :: A global unique identifier for the Node.
        # @param name: <i>str</i> :: The displayed name of the Node.
        # @param x: <i>float</i> :: The x-coordinate of the Node. Assumes a web-standard grid with (0,0) at (top,left)
        # @param y: <i>float</i> :: The y-coordinate of the Node. Assumes a web-standard grid with (0,0) at (top,left)
        # @param shape: <i>int</i> :: The number of sides the Node should have. 0 for circle, 1 for image.
        # @param image: <i>str</i> :: The url of an image to display on this node. Requires a shape of 1.
        # @param radius: <i>float</i> :: The radius of the Node shape.
        # @param color: <i>str</i> :: A color string, e.g. '#FF0000'. 'dynamic' will make the Node responsive to user-selected palette.  'static' will leave a node image's color unaffected.  Labeled as a Photo mode in the gui.
        #
        # @code
        # n = Node(name='My Node', shape=8, radius=33.5)
        # g.add_node(n)
        # @endcode
        if not uid:
            uid = str(uuid.uuid4())
        ## <i>str</i> :: The display name of the Node.
        self.name = urllib.unquote(name)

        ## <i>str</i> :: The global unique id of the Node.
        self.uid = urllib.unquote(uid)

        ## <i>float</i> :: The x-coordinate of the Node. Assumes a web-standard grid with (0,0) at (top,left)
        self.x = float(x)

        ## <i>float</i> :: The y-coordinate of the Node. Assumes a web-standard grid with (0,0) at (top,left)
        self.y = float(y)

        ## <i>int</i> :: The number of sides of the Node shape. 0 for circle, 1 for image, otherwise n-gon.
        self.shape = int(shape)

        ## <i>str</i> :: The URL for an image to display on this Node.
        self.image = urllib.unquote(image)

        ## <i>float</i> :: The radius of the Node
        self.radius = radius

        ## <i>str</i> :: The color of the Node. e.g. '#FF0000'
        self.color = urllib.unquote(color)

        ## <i>bool</i> :: Whether or not this Node has been created on the Server.
        self.created = False

    ## <i>Graph</i> :: The Graph to which this Node belongs.
    graph = None

    def add_detail(self, detail, update=True, callback=None):
        ##
        # Attaches a Detail to this Node.  Allows for fewer explicit property declarations on Detail creation.
        #
        # @param detail: <i>Detail</i> :: The Detail to attach to this Node.
        # @param update: <i>bool</i> :: Whether or not to immediately enqueue the query.
        # @param callback: <i>function</i> :: An optional function to handle the server's response to the query.
        #
        # @code
        # d = Detail(content="http://psymphonic.com", type="link")
        # n.add_detail(d)
        # @endcode
        detail.anchor_type = self.__class__.__name__.lower()
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
        ##
        # Returns a uid-keyed dictionary of Detail objects which are attached to this Node.
        #
        # @return dets: <i>dict</i> :: A uid-keyed dictionary of Detail objects which are attached to this Node.
        #
        # @code
        # for d in n.details():
        #     print n.details()[d].anchor() == n # True
        # @endcode
        dets = {}
        for d in self.graph.detail_list():
            if d.anchor_uid == self.uid:
                dets[d.uid] = d
        return dets

    def detail_list(self):
        ##
        # Returns a list of Detail objects which are attached to this Node.
        #
        # @return dets: <i>list</i> :: A list of Detail objects which are attached to this Node.
        #
        # @code
        # for d in n.detail_list():
        #     print d.anchor() == n # True
        # @endcode
        dets = []
        for d in self.graph.detail_list():
            if d.anchor_uid == self.uid:
                dets.append(d)
        return dets

    def out_links(self):
        ##
        # Returns a list of Link objects which originate at this Node.
        #
        # @return links: <i>list</i> :: A list of Link objects which originate at this Node.
        #
        # @code
        # for link in n.out_links():
        #     print link.value
        # @endcode
        links = []
        for link in self.graph.link_list():
            if link.origin_uid == self.uid:
                links.append(link)
        return links

    def in_links(self):
        ##
        # Returns a list of Link objects which terminate at this Node.
        #
        # @return links: <i>list</i> :: A list of Link objects which terminate at this Node.
        #
        # @code
        # for link in n.in_links():
        #     print link.value
        # @endcode
        links = []
        for link in self.graph.link_list():
            if link.terminus_uid == self.uid:
                links.append(link)
        return links

    def all_links(self):
        ##
        # Returns a list of Link objects which connect to this Node.
        #
        # @return links: <i>list</i> :: A list of Link objects which connect to this Node.
        #
        # @code
        # for link in n.all_links():
        #     print link.value
        # @endcode
        links = []
        for link in self.graph.link_list():
            if link.origin_uid == self.uid or link.terminus_uid == self.uid:
                links.append(link)
        return links

    def out_neighbors(self):
        ##
        # Returns a list of Node objects which neighbor this Node by outgoing Link.
        #
        # @return nodes: <i>list</i> :: A list of Node objects which neighbor this Node by outgoing Link.
        #
        # @code
        # for n2 in n.out_neighbors():
        #     print n2.name
        # @endcode
        neighbors = []
        for link in self.graph.link_list():
            if link.origin_uid == self.uid:
                neighbors.append(link.terminus())
        return neighbors

    def in_neighbors(self):
        ##
        # Returns a list of Node objects which neighbor this Node by incoming Link.
        #
        # @return nodes: <i>list</i> :: A list of Node objects which neighbor this Node by incoming Link.
        #
        # @code
        # for n2 in n.in_neighbors():
        #     print n2.name
        # @endcode
        neighbors = []
        for link in self.graph.link_list():
            if link.terminus_uid == self.uid:
                neighbors.append(link.origin())
        return neighbors

    def all_neighbors(self):
        ##
        # Returns a list of Node objects which neighbor this Node.
        #
        # @return nodes: <i>list</i> :: A list of Node objects which neighbor this Node.
        #
        # @code
        # for n2 in n.all_neighbors():
        #     print n2.name
        # @endcode
        neighbors = []
        for link in self.graph.link_list():
            if link.terminus_uid == self.uid:
                neighbors.append(link.origin())
            elif link.origin_uid == self.uid:
                neighbors.append(link.terminus())
        return neighbors

    def dictionary(self):
        ##
        # Returns a dictionary with this Node's properties, as required by the API. Generally used to build queries.
        #
        # @return dict: <i>dict</i> :: A dictionary of this Node's properties.
        #
        # @code
        # q = n.dictionary()
        # q['query'] = 'newnode'
        # g.queue(q)
        # @endcode
        return {'uid': urllib.quote(self.uid),
                'name': urllib.quote(self.name),
                'x': str(self.x),
                'y': str(self.y),
                'radius': self.radius,
                'shape': str(self.shape),
                'picture': urllib.quote(self.image),
                'color': urllib.quote(self.color)}

    def update(self, callback=None):
        ##
        # Updates the register of this Node on the server.
        #
        # @param callback: <i>function</i> ::  An optional function to handle the server's response to the query.
        #
        # @code
        # n.name = "Different Node Name"
        # n.radius += 5
        # n.update()
        # @endcode
        q = self.dictionary()
        q['query'] = "updatenode"
        self.graph.queue(q, callback)

##
# Links connect Node objects to each other. They have a LinkType.  Detail objects can be attached to them.
#
class Link():
    def __init__(self, origin_uid, terminus_uid, type, name="Link", value=1, uid=None):
        ##
        # Constructs a Link object.
        #
        # @param origin_uid: <i>str</i> :: The uid of the origin Node.
        # @param terminus_uid: <i>str</i> :: The uid of the terminus Node.
        # @param type: <i>str</i> :: The name of the LinkType that describes this Link.
        # @param name: <i>str</i> :: The displayed name of this Link.
        # @param value: <i>int</i> :: The value of this Link.
        # @param uid: <i>str</i> :: The global unique identifier of this Link.
        #
        # @code
        # my_link = Link(origin_node.uid, terminus_node.uid, 'Money', value=60)
        # g.add_link(l)
        # @endcode
        if not uid:
            uid = str(uuid.uuid4())

        ## <i>str</i> :: The global unique id of the origin node.
        self.origin_uid = urllib.unquote(origin_uid)

        ## <i>str</i> :: The global unique id of the terminus node.
        self.terminus_uid = urllib.unquote(terminus_uid)

        ## <i>str</i> :: The name of the LinkType of this Link
        self.type = urllib.unquote(type)

        ## <i>str</i> :: The display name of this Link
        self.name = urllib.unquote(name)

        ## <i>int</i> :: The value of this Link, between 1 and the LinkType.max
        self.value = int(value)

        ## <i>str</i> :: The global unique id of this Link
        self.uid = urllib.unquote(uid)

        ## <i>bool</i> :: Whether or not this Link has been created on the server.
        self.created = False

    ## <i>Graph</i> :: The Graph to which this Link belongs.
    graph = None

    def link_type(self):
        ##
        # Returns the LinkType object that this Link is a member of.
        #
        # @return link_type: <i>LinkType</i> ::
        #
        # @code
        # print link.link_type().color
        # @endcode
        return self.graph.link_type(self.type)

    def add_detail(self, detail, update=True, callback=None):
        ##
        # Attaches a Detail to this Link.
        #
        # @param detail: <i>Detail</i> :: The Detail to attach to this Link.
        # @param update: <i>bool</i> :: Whether or not to immediately enqueue the query.
        # @param callback: <i>function</i> :: An optional function to handle the server's response to the query.
        #
        # @code
        # d = Detail(content="http://psymphonic.com", type="link")
        # l.add_detail(d)
        # @endcode
        detail.anchor_type = 'rel'
        detail.anchor_uid = self.uid
        if not detail.x:
            detail.x = self.center()['x']+10
        if not detail.y:
            num = 0
            for d in self.graph.detail_list():
                if d.anchor_uid == self.uid:
                    num += 1
            detail.y = self.center()['y']+(20*num)
        self.graph.add_detail(detail, update=update, callback=callback)

    def detail_list(self):
        ##
        # Returns a list of Detail objects which are attached to this Link.
        # 
        # @return details: <i>list</i> :: A list of Detail objects which are attached to this Link. 
        #
        # @code
        # for d in n.detail_list():
        #     print d.anchor() == n # True
        # @endcode
        dets = []
        for d in self.graph.detail_list:
            if d.anchor_uid == self.uid:
                dets.append(d)
        return dets

    def details(self):
        ##
        # Returns a uid-keyed dictionary of Detail objects which are attached to this Link.
        # 
        # @return details: <i>dict</i> :: A uid-keyed dictionary of Detail objects which are attached to this Link. 
        #
        # @code
        # for d in n.details():
        #     print n.details()[d].anchor() == n # True
        # @endcode
        dets = {}
        for d in self.graph.detail_list:
            if d.anchor_uid == self.uid:
                dets[d.uid] = d
        return dets

    def dictionary(self):
        ##
        # Returns a dictionary of this Link's properties, as required by the API. Generally used internally to build queries.
        # 
        # @return dict: <i>dict</i> :: A dictionary of this Link's properties. 
        #
        # @code
        # q = n.dictionary()
        # q['query'] = 'newnode'
        # g.queue(q)
        # @endcode
        return {'uid': urllib.quote(self.uid),
                'name': urllib.quote(self.name),
                'value': str(self.value),
                'rel_type': urllib.quote(self.type),
                'o_uid': urllib.quote(self.origin_uid),
                't_uid': urllib.quote(self.terminus_uid)}

    def origin(self):
        ##
        # Returns the origin Node.
        # 
        # @return origin: <i>Node</i> :: 
        #
        # @code
        # print link.origin().name
        # @endcode
        return self.graph.node(self.origin_uid)

    def parallel(self):
        ##
        # Returns a list of Links which are parallel to this Link, meaning that they share two nodes, regardless of direction.
        # 
        # @return links: <i>list</i> :: A list of Links which are parallel to this Link.
        #
        # @code
        # total_value = 0
        # for l2 in l.parallel():
        #     total_value += l2
        # print total_value
        # @endcode
        ps = []
        for link in self.graph.link_list():
            if link.origin_uid == self.origin_uid and link.terminus_uid == self.terminus_uid:
                ps.append(link)
            elif link.origin_uid == self.terminus_uid and link.terminus_uid == self.origin_uid:
                ps.append(link)
        return ps

    def terminus(self):
        ##
        # Returns the terminus Node.
        # 
        # @return terminus: <i>Node</i> :: 
        #
        # @code
        # print link.terminus().name
        # @endcode
        return self.graph.node(self.terminus_uid)

    def update(self, callback=None):
        ##
        # Updates the server's registry of this Link.
        #
        # @param callback: <i>function</i> :: An optional function to handle the server's response to the query.
        #
        # @code
        # l.value += 1
        # l.name = "New Link Name"
        # l.update()
        # @endcode
        q = self.dictionary()
        q['query'] = "updaterel"
        self.graph.queue(q, callback)

    def center(self):
        ##
        # Returns the center point of this Link.
        #
        # @return point: <i>dict</i> :: A dictionary {x,y} identifying the center of this Link.
        #
        # @code
        # if link.center()['x'] > 42:
        #     print link.center()['y']
        # @endcode
        x = (self.origin().x+self.terminus().x)/2
        y = (self.origin().y+self.terminus().y)/2
        return {'x': x, 'y': y}

##
# LinkType objects define the parameters of Link objects.
#
class LinkType:
    def __init__(self, name='Links', icon='img/link_icon.png', tile='img/link_tile.png', color='dynamic', max=10, sync=True):
        ##
        # Constructs a LinkType object.
        #
        # @param name: <i>str</i> :: The name of this LinkType.
        # @param icon: <i>str</i> :: A URL for the icon to display for this LinkType
        # @param tile: <i>str</i> :: A URL for the image to tile on the tiling sprite for this LinkType
        # @param color: <i>str</i> :: A color string, e.g '#FF0000' for this LinkType. 'dynamic' will make this LinkType responsive to the user palette.
        # @param max: <i>int</i> :: The maximum value allowed for this LinkType
        # @param sync: <i>bool</i> :: Whether the icons for this LinkType should reflect the color of the line.  Default True.
        #
        # @code
        # lt = LinkType()
        # g.add_link_type(lt)
        # @endcode

        ## <i>str</i> :: The display name of this LinkType. Will show in the Legend, and is a displayable property on Link Labels.
        self.name = urllib.unquote(name)

        ## <i>str</i> :: The URL of the image to display as the Icon for this LinkType. Should be 24x21 pixels with a transparent background.
        self.icon = urllib.unquote_plus(icon)

        ## <i>str</i> :: The URL of the image to display as the Icon for this LinkType. Should be 100x21 pixels with a transparent background.
        self.tile = urllib.unquote_plus(tile)

        ## <i>str</i> :: The color of this LinkType. e.g. "#FF0000"
        self.color = urllib.unquote(color)

        ## <i>int</i> :: The maximum value any Link of this LinkType can possess.
        self.max = int(max)

        self.sync = sync

        ## <i>bool</i> :: Whether or not this LinkType has been created on the server.
        self.created = False

    ## <i>Graph</i> :: The Graph to which this LinkType belongs.
    graph = None

    def dictionary(self):
        ##
        # Returns a dictionary of this LinkType's properties, as required by the API. Generally used internally to build queries.
        # 
        # @return dict: <i>dict</i> ::  
        #
        # @code
        # q = lt.dicitonary()
        # q['query'] = 'newreltype'
        # @endcode
        return {'NAME': urllib.quote(self.name),
                'ICON': urllib.quote_plus(self.icon),
                'TILE': urllib.quote_plus(self.tile),
                'COLOR': urllib.quote(self.color),
                'MAX': self.max,
                'SYNC': self.sync}

    def update(self, callback=None):
        ##
        # Updates the server's registry of this LinkType
        #
        # @param callback: <i>function</i> :: An optional function to handle the server's response to the query.
        #
        # @code
        # lt.max += 5
        # lt.color = "#FF0000"
        # lt.update()
        # @endcode
        q = self.dictionary()
        q['query'] = "updatereltype"
        self.graph.queue(q, callback)

    def links(self):
        ##
        # Returns all Link objects in the graph that have this LinkType
        #
        # @return list: <i>list</i> :: A list of Link objects which have this LinkType.
        #
        # @code
        # money_links = g.link_type('Money').links()
        # for link in money_links:
        #     print link.origin().name+"--$"+str(link.value)+"-->"+link.terminus().name
        # @endcode
        ls = []
        for link in self.graph.links():
            if link.type == self.name:
                ls.append(link)
        return ls

##
# Detail objects contain links or text, and can be attached to Node objects and Link objects.
#
class Detail:
    def __init__(self, content, anchor_uid=None, anchor_type=None, x=None, y=None, type='comment', name=None, uid=None):
        ##
        # Constructs a Detail object.
        #
        # @param content: <i>str</i> :: The content of this Detail.
        # @param anchor_uid: <i>str</i> :: The uid of the object this Detail is attached to.
        # @param anchor_type: <i>str</i> :: The type of object this Detail is attached to.
        # @param x: <i>float</i> :: The x-coordinate of this Detail.
        # @param y: <i>float</i> :: The y-coordinate of this Detail.
        # @param type: <i>str</i> :: The type of Detail this is. 'link', 'comment', 'video', 'image'
        # @param name: <i>str</i> :: The name of this Detail. This is not currently used for anything on the front-end.
        # @param uid: <i>str</i> :: A global unique identifier for this Detail.
        #
        # @code
        # d = Detail("http://psymphonic.com/", type="link")
        # n.add_detail(d)
        # @endcode
        if not uid:
            uid = str(uuid.uuid4())
        if anchor_uid:
            anchor_uid = urllib.unquote(anchor_uid)

        ## <i>str</i> :: The global unique identifier of the object this Detail is anchored to.
        self.anchor_uid = anchor_uid

        ## <i>str</i> :: The type of object this Detail is anchored to.
        self.anchor_type = anchor_type

        ## <i>str</i> :: The content of this Detail.
        self.content = urllib.unquote_plus(content)

        if x:
            x = float(x)
        ## <i>float</i> :: The x-coordinate of the Detail.
        self.x = x

        if y:
            y = float(y)
        ## <i>float</i> :: The y-coordinate of the Detail.
        self.y = y

        ## <i>str</i> :: The type of this detail. 'link', 'comment', 'image', 'video'
        self.type = type

        if name:
            name = urllib.unquote(name)
        else:
            name = ' '
        ## <i>str</i> :: The name of this detail.  Currently not used on the front end.
        self.name = name

        ## <i>str</i> :: The global unique identifier of this Detail
        self.uid = urllib.unquote(uid)

        ## <i>bool</i> :: Whether or not this Detail has been created on the server.
        self.created = False

    ## <i>Graph</i> :: The Graph to which this Detail belongs.
    graph = None

    def anchor(self):
        ##
        # Returns the object this Detail is anchored to.
        #
        # @return object: <i>Node|Link</i> ::
        #
        # @code
        # for d in g.detail_list():
        #     print d.anchor().name
        # @endcode
        if self.anchor_type == "Node" or self.anchor_type == "node":
            return self.graph.node(self.anchor_uid)
        elif self.anchor_type == "rel":
            return self.graph.link(self.anchor_uid)

    def dictionary(self):
        ##
        # Returns a dictionary of this LinkType's properties, as required by the API. Generally used internally to build queries.
        #
        # @return dict: <i>dict</i> ::
        #
        # @code
        # q = d.dictionary()
        # q['query'] = "newdetail"
        # g.queue(q)
        # @endcode
        return {'anchor_uid': urllib.quote(self.anchor_uid),
                'anchor_type': self.anchor_type,
                'uid': urllib.quote(self.uid),
                'name': urllib.quote(self.name),
                'content': urllib.quote_plus(self.content),
                'type': self.type,
                'x': str(self.x),
                'y': str(self.y)}

    def update(self, callback=None):
        ##
        # Updates the server's registry of this Detail
        #
        # @param callback: <i>function</i> :: An optional function to handle the server's response to the query.
        #
        # @code
        # d.content = "http://en.wikipedia.org/wiki/Christopher_Alexander"
        # d.update()
        # @endcode
        q = self.dictionary()
        q['query'] = "updatedetail"
        self.graph.queue(q, callback)


def create_graph(name, url, username, key):
    ##
    # Creates a new Graph that you can access through Psynth.
    #
    # @param name: <i>str</i> :: The name of the Graph to create.
    # @param url: <i>str</i> :: The base URL for your Psynth server. e.g. https://psynth.psymphonic.com
    # @param username: <i>str</i> :: Your Psynth username
    # @param key: <i>str</i> :: Your Psynth API key.
    # @return graph: <i>Graph</i> ::
    #
    # @code
    # g = create_graph(
    #     name='my graph',
    #     url='https://psynth.psymphonic.com/',
    #     username='me@company.com',
    #     key='myapikey'
    # )
    # @endcode
    g = Graph(name=name,
              url=url,
              username=username,
              key=key,
              filename='')
    c = requests.get(g.prep({'query': 'createmap',
                             'name': g.name}), verify=False)
    if c.status_code == 200:
        cr = c.json()
        g.filename = cr['filename']
        return g
    elif c.status_code == 406:
        print c.url+"    "+c.json()
    else:
        print c.url+"    "+str(c.status_code)


def load_graph(filename, url, username, key):
    ##
    # Loads a Graph from the server.
    #
    # # @param filename: <i>str</i> :: The global unique filename of the Graph to load.
    # # @param url: <i>str</i> :: The base URL for your Psynth server. e.g. https://psynth.psymphonic.com
    # # @param username: <i>str</i> :: Your Psynth username
    # # @param key: <i>str</i> :: Your Psynth API key.
    # # @return graph: <i>Graph</i> ::
    #
    # @code
    # g = load_graph(
    #     filename='myfile.gt',
    #     url='https://psynth.psymphonic.com/',
    #     username='me@company.com',
    #     key='myapikey'
    # )
    # @endcode
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
        for link in ls:
            ll = Link(name=link['NAME'],
                      type=link['TYPE'],
                      value=link['VALUE'],
                      origin_uid=link['ORIGIN'],
                      terminus_uid=link['TERMINUS'],
                      uid=link['UID'])
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