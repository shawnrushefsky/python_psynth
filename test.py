__author__ = 'psymac0'
import pyPsynth
from random import randint



g = pyPsynth.create_graph(
    name='api detail test',
    url='https://10.0.1.30/',
    username='shawn@psymphonic.com',
    key='9a6b250e-f9b3-4caf-81ae-14a062e15674'
)
n = pyPsynth.Node(x=300, y=300)
g.add_node(n)
for i in range(1,6):
    d = pyPsynth.Detail("http://psymphonic.com", type='link')
    n.add_detail(d)


