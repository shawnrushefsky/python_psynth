__author__ = 'psymac0'
import psynth
from random import randint



g = psynth.create_graph(
    name='api test',
    url='https://10.0.1.30/',
    username='shawn@psymphonic.com',
    key='9a6b250e-f9b3-4caf-81ae-14a062e15674'
)
for i in range(1,10):
    n = psynth.Node(name='Node '+str(i))
    g.add_node(n)
ns = g.node_list()
lt = psynth.LinkType()
g.add_link_type(lt)
for i in range(1,30):
    origin = randint(0, len(ns)-1)
    terminus = randint(0, len(ns)-1)
    while terminus == origin:
        terminus = randint(0, len(ns)-1)
    link = psynth.Link(ns[origin].uid, ns[terminus].uid, lt.name, value=randint(1, lt.max))
    g.add_link(link)
for node in ns:
    for i in range(0, 3):
        d = psynth.Detail("http://psymphonic.com", type='link')
        node.add_detail(d)
for link in g.link_list():
    for i in range(0, 3):
        d = psynth.Detail("http://psymphonic.com", type='link')
        link.add_detail(d)
g.draw()



