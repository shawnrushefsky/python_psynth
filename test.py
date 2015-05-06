__author__ = 'psymac0'
import psynth



g = psynth.create_graph(
    name='psynth test',
    url='https://10.0.1.30/',
    username='shawn@psymphonic.com',
    password='conductor'
)

print g.filename