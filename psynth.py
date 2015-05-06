__author__ = 'psymac0'
import urllib
import simplejson as json
import uuid
import requests


file_queries = ['createmap', 'getfilelist', 'renamemap', 'addusertomap']
app_queries = ['getwholegraph', 'newnode', 'batchnodes', 'delnode', 'newrel', 'batchrels', 'delrel', 'updatenode',
               'updaterel', 'newdetail', 'deldetail', 'updatedetail', 'tag', 'newcomment', 'getcomments',
               'setdrawparams', 'drawgraph', 'nodeplusone', 'interconnections', 'expandselection', 'setgraphname',
               'getgraphname', 'sessionquit', 'saveprefs', 'getheat', 'newreltype', 'updatereltype', 'shortestpath',
               'chatmessage', 'getchat', 'getqueue', 'getallpos', 'exporttoimage']


def make_diagram(name):
    return {'query': 'createmap',
             'name': urllib.quote(name)}


class Graph:
    nodes = []
    nodeIndex = {}
    links = []
    linkIndex = {}
    details = []
    detailIndex = {}
    linktypes = {}

    def __init__(self, name, filename, url, username, password):
        self.name = name
        self.filename = filename
        self.url = url
        self.username = username
        self.password = password

    def id_tag(self, obj):
        obj['user'] = self.username
        obj['password'] = self.password
        obj['filename'] = self.filename
        return obj

    def prep(self, query):
        query = self.id_tag(query)
        if query['query'] in file_queries:
            url = self.url+'p/'+json.dumps(query)
        elif query['query'] in app_queries:
            url = self.url+'crunch/'+json.dumps(query)
        else:
            return False
        return url


class Node:
    def __init__(self, uid="default", name="New Node", x=1, y=1, shape=6, picture="na", radius=24, color="default"):
        if uid == "default":
            uid = str(uuid.uuid4())
        self.name = str(name)
        self.uid = uid
        self.x = x
        self.y = y
        self.shape = shape
        self.picture = picture
        self.radius = radius
        self.color = color


def create_graph(name, url, username, password):
    g = Graph(name=name, url=url, username=username, password=password, filename='')
    c = requests.get(g.prep(make_diagram("Insurgents 1776")), verify=False)
    cr = c.json()
    g.filename = cr['filename']
    return g