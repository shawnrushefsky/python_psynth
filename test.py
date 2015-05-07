__author__ = 'psymac0'
import pyPsynth
from random import randint



g = pyPsynth.load_graph(
    filename='182b3149-abce-4eaf-927d-5954feb647c3.gt',
    url='https://10.0.1.30/',
    username='shawn@psymphonic.com',
    key='9a6b250e-f9b3-4caf-81ae-14a062e15674'
)
print g.name
print str(len(g.node_list()))+" nodes."
print str(len(g.link_list()))+" links."
for n in g.node_list():
    print n.name
