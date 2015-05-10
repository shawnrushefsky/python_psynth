__author__ = 'psymac0'
from psynth import *
from random import randint


# Create a Graph
g = create_graph(
    name='api test',
    url='http://psynth.psymphonic.com/',
    username='user@company.com',
    key='yourapikey'
)

# Create 10 Nodes
for i in range(0,10):
    n = Node(name='Node '+str(i))
    g.add_node(n)

# Grab a list of all the Nodes.
ns = g.node_list()

# Create a default LinkType
lt = LinkType()
g.add_link_type(lt)

# Create 30 random Links.
for i in range(0,30):
    origin = randint(0, len(ns)-1)
    terminus = randint(0, len(ns)-1)
    while terminus == origin:
        terminus = randint(0, len(ns)-1)
    link = Link(ns[origin].uid, ns[terminus].uid, lt.name, value=randint(1, lt.max))
    g.add_link(link)

# Put 3 Details on each Node.
for node in ns:
    for i in range(0, 3):
        d = Detail("http://psymphonic.com", type='link')
        node.add_detail(d)

# Put 3 Details on each Link
for link in g.link_list():
    for i in range(0, 3):
        d = Detail("http://psymphonic.com", type='link')
        link.add_detail(d)

# Calculate the layout of the Graph
g.draw()



