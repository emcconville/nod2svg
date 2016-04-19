from __future__ import print_function
import math
import plistlib
import sys
import xml.etree.cElementTree as ET

all = ('NodalImage',
       'VERSION',
       'main')

NODE = 'Node'
NOTE = 'Note'
STYLE_ANNOTATION_COLOR = 'StyleAnnotationColor'
AUTHOR = 'Author'
STYLE_BACK_GROUNDCOLOR = 'StyleBackgroundColor'
COMMENT = 'Comment'
DONT_PLAY_NOTE = 'DontPlay' + NOTE
EDGE = 'Edge'
ELEMENTS = 'Elements'
FROM_NODE = 'From' + NODE
PATH = 'Path'
TEXT = 'Text'
TEXTBOX = TEXT + 'Box'
TICKPOS = 'TickPos'
TITLE = 'Title'
TO_NODE = 'To' + NODE
TYPE = 'Type'
WORMHOLE = 'IsWormhole'
X = 'X'
Y = 'Y'
GRID_TICK = 166320

VERSION = '0.1.0'

class NodalImage(object):
    VERSION = VERSION
    elements = {}
    edges = {}
    nodes = {}
    textboxes = {}
    bg = 'transparent'
    ec = '#717589ff'
    nc = '#9b9effff'
    ac = '#ffffff80'

    mbr = [99999999999999,
           99999999999999,
           -99999999999999,
           -99999999999999]

    def __init__(self, path=None):
        if path:
            self.load(path)

    def load(self, path):
        with open(path, 'rb') as fd:
            nod = plistlib.readPlist(fd)
            if ELEMENTS in nod:
                self.elements = nod[ELEMENTS]
            if AUTHOR in nod:
                self.author = nod[AUTHOR]
            if TITLE in nod:
                self.title = nod[TITLE]
            if COMMENT in nod:
                self.comment = nod[COMMENT]
            if STYLE_BACK_GROUNDCOLOR in nod:
                self.bg = nod[STYLE_BACK_GROUNDCOLOR]
            if STYLE_ANNOTATION_COLOR in nod:
                self.ac = nod[STYLE_ANNOTATION_COLOR]
        self.nodes = self.lookup(TYPE, NODE)
        self.edges = self.lookup(TYPE, EDGE)
        self.textboxes = self.lookup(TYPE, TEXTBOX)

    def lookup(self, attr, val):
        matches = {}
        for key in self.elements:
            node = self.elements[key]
            if attr in node and node[attr] == val:
                matches[key] = node
        return matches

    def parseTickPos(self, attr):
        attr = attr.lstrip('{').rstrip('}')
        return attr.split(', ')

    def growMBR(self, x, y):
        ix = int(x)
        iy = int(y)
        if ix > self.mbr[2]:
            self.mbr[2] = ix
        if ix < self.mbr[0]:
            self.mbr[0] = ix
        if iy > self.mbr[3]:
            self.mbr[3] = iy
        if iy < self.mbr[1]:
            self.mbr[1] = iy
        return ix, iy

    @property
    def background_color(self):
        return self.bg[:7]

    @property
    def background_opacity_color(self):
        return '{0:.2f}'.format(int(self.bg[-2:],16) / 256.0)

    @property
    def node_color(self):
        return self.nc[:7]

    @property
    def node_opacity_color(self):
        return '{0:.2f}'.format(int(self.nc[-2:],16) / 256.0)

    @property
    def node_fill_color(self):
        return self.nc[:7]

    @property
    def node_fill_opacity_color(self):
        # Note this defaults to 16% of given alpha
        given_alpha = int(self.nc[-2:],16) / 256.0
        return '{0:.2f}'.format(given_alpha * 0.16)

    @property
    def edge_color(self):
        return self.ec[:7]

    @property
    def edge_opacity_color(self):
        return '{0:.2f}'.format(int(self.ec[-2:],16) / 256.0)

    @property
    def annotation_color(self):
        return self.ac[:7]

    @property
    def annotation_opacity_color(self):
        return '{0:.2f}'.format(int(self.ac[-2:],16) / 256.0)

    def generate_nodes(self, root):
        group = ET.SubElement(root, 'g')
        n = self.nodes
        for k in n:
            v = n[k]
            x, y = self.parseTickPos(v[TICKPOS])
            v[X], v[Y] = self.growMBR(x, y)

            dot_attr = {'cx': x,
                        'cy': y,
                        'r': '64000',
                        'fill': self.node_fill_color,
                        'fill-opacity': self.node_fill_opacity_color,
                        'stroke': self.node_color,
                        'stroke-opacity': self.node_opacity_color,
                        'stroke-width': '6400'}
            dot = ET.SubElement(group, 'circle', **dot_attr)
            if DONT_PLAY_NOTE in v and v[DONT_PLAY_NOTE]:
                dot.attrib['stroke-dasharray'] = '32000 12800'
            if v['SignallingMethod'] == 'Parallel':
                use_attr = {'xlink:href': '#parallel_head',
                            'x': x,
                            'y': y}
                use = ET.SubElement(group,'use', **use_attr)
            elif v['SignallingMethod'] == 'Random':
                use_attr = {'xlink:href': '#random_head',
                            'x': x,
                            'y': y}
                use = ET.SubElement(group,'use', **use_attr)

    def path_vertical(self, start, end):
        if start[Y] > end[Y]:
            start_y = start[Y] - 64000
        else:
            start_y = start[Y] + 64000
        if end[Y] > start[Y]:
            end_y = end[Y] - 70400
        else:
            end_y = end[Y] + 70400
        return 'M {0} {1} V {2}'.format(start[X], start_y, end_y)

    def path_horizontal(self, start, end):
        if start[X] > end[X]:
            start_x = start[X] - 64000
        else:
            start_x = start[X] + 64000
        if end[X] > start[X]:
            end_x = end[X] - 70400
        else:
            end_x = end[X] + 70400
        return 'M {0} {1} H {2}'.format(start_x, start[Y], end_x)

    def path_city_block(self, start, end):
        if start[X] == end[X]:
            path = self.path_vertical(start, end)
        elif start[Y] == end[Y]:
            path = self.path_horizontal(start, end)
        else:
            if end[Y] > start[Y]:
                end_y = end[Y] - 70400
            else:
                end_y = end[Y] + 70400
            if start[X] > end[X]:
                start_x = start[X] - 64000
            else:
                start_x = start[X] + 64000
            path = "M {0} {1} H {2} V {3}".format(start_x,
                                                  start[Y],
                                                  end[X],
                                                  end_y)
        return path

    def path_city_block_flipped(self, start, end):
        if start[X] == end[X]:
            path = self.path_vertical(start, end)
        elif start[Y] == end[Y]:
            path = self.path_horizontal(start, end)
        else:
            if start[Y] > end[Y]:
                start_y = start[Y] - 64000
            else:
                start_y = start[Y] + 64000
            if end[X] > start[X]:
                end_x = end[X] - 70400
            else:
                end_x = end[X] + 70400
            path = "M {0} {1} V {2} H {3}".format(start[X],
                                                  start_y,
                                                  end[Y],
                                                  end_x)
        return path

    def path_direct(self, start, end):
        dy = end[Y] - start[Y]
        dx = end[X] - start[X]
        theta = math.atan2(-dy, -dx)
        theta %= 2 * math.pi
        theta_cos = math.cos(theta)
        theta_sin = math.sin(theta)
        end_x = end[X] + 70400 * theta_cos
        end_y = end[Y] + 70400 * theta_sin
        start_x = start[X] - 64000 * theta_cos
        start_y = start[Y] - 64000 * theta_sin
        return  "M {0} {1} L {2} {3}".format(start_x,
                                             start_y,
                                             end_x,
                                             end_y)

    def generate_edges(self, root):
        g_edges = ET.SubElement(root, 'g')
        e = self.edges
        for k in e:
            v = e[k]
            start = self.nodes['{0}'.format(v[FROM_NODE])]
            end = self.nodes['{0}'.format(v[TO_NODE])]

            if v[PATH] == 'Direct':
                path = self.path_direct(start, end)
            elif v[PATH] == 'CityBlock':
                path = self.path_city_block(start, end)
            elif v[PATH] == 'CityBlockFlipped':
                path = self.path_city_block_flipped(start, end)
            else:
                continue

            line_attr = {'d': path,
                         'fill': 'transparent',
                         'marker-end': 'url(#arrow_head)',
                         'stroke': self.edge_color,
                         'stroke-opacity': self.edge_opacity_color,
                         'stroke-width': '6400'}
            line = ET.SubElement(g_edges, 'path', **line_attr)
            if WORMHOLE in v and v[WORMHOLE]:
                line.attrib['stroke-dasharray'] = '32000 12800'

    def generate_text_boxes(self, root):
        texts = self.textboxes
        g_text = ET.SubElement(root, 'g')
        w3_uri = 'http://www.w3.org/1999/xhtml'
        fo_attr = {'width': '100%',
                   'height': '100%',
                   'stroke': self.annotation_color,
                   'stroke-opacity': self.annotation_opacity_color,
                   'requiredExtensions': w3_uri}
        for k in texts:
            v = texts[k]
            x, y = self.parseTickPos(v[TICKPOS])
            v[X], v[Y] = self.growMBR(x, y)
            html = ET.fromstring(v[TEXT])
            #  Poorly attempt to scale text up to a level that can be viewed.
            t = 'scale(5000) translate({}, {})'.format(-v[X] * 0.999785,
                                                       -v[Y] * 0.999795)
            fobject = ET.SubElement(g_text,
                                   'foreignObject',
                                   x=x,
                                   y=y,
                                   transform=t,
                                   **fo_attr)
            html.attrib['xmlns'] = w3_uri
            fobject.append(html)

    def generate(self):
        svg_attr = {'xmlns': 'http://www.w3.org/2000/svg',
                    'xmlns:xlink': 'http://www.w3.org/1999/xlink',
                    'version': '1.1',
                    'style': 'background:{};'.format(self.background_color)}
        svg = ET.Element('svg',
                         **svg_attr)
        defs = ET.SubElement(svg, 'defs')
        # Arrow head
        maker_attr = {'id': 'arrow_head',
                      'orient': 'auto',
                      'markerWidth': '6',
                      'markerHeight': '6',
                      'refX': '5.0',
                      'refY': '3'}
        maker = ET.SubElement(defs, 'marker', **maker_attr)
        path_attr = {'d': 'M 0 0 V 6 L 6 3 Z',
                     'fill': self.edge_color,
                     'fill-opacity': self.edge_opacity_color}
        path = ET.SubElement(maker,
                             'path',
                             **path_attr)
        # Random head (X mark)
        # Path needs to be re-calculated
        # data = 'M 20000 2000 L 85000 70000 M 2000 20000 L 70000 85000'
        data = 'M 33408 16704 L 50112 66752 M 16704 33408 L 66752 50112'

        random_attr = {'d': data,
                       'id': 'random_head',
                       'stroke': self.node_color,
                       'stroke-opacity': self.node_opacity_color,
                       'stroke-width': '6400'}
        path = ET.SubElement(defs,
                             'path',
                             **random_attr)
        # Parallel head (|| mark)
        # Path needs to be re-calculated
        # data = 'M 32000 6400 L 58000 82000 M 6400 32000 L 82000 58000'
        data = 'M 27840 16704 L 72320 55680 M 11136 27840 L 55680 66752'
        parallel_attr = {'d': data,
                     'id': 'parallel_head',
                     'stroke': self.node_color,
                     'stroke-opacity': self.node_opacity_color,
                     'stroke-width': '6400'}
        path = ET.SubElement(defs,
                             'path',
                             **parallel_attr)
        self.generate_nodes(svg)
        self.generate_edges(svg)
        self.generate_text_boxes(svg)
        self.mbr[0] -= GRID_TICK
        self.mbr[1] -= GRID_TICK
        self.mbr[2] += GRID_TICK
        self.mbr[3] += GRID_TICK
        t, l, w, h = self.mbr
        w = abs(t) + abs(w)
        h = abs(l) + abs(h)
        svg.attrib['viewBox'] = '{0} {1} {2} {3}'.format(t, l , w, h)
        return svg

    def dump(self, path):
        root = self.generate()
        tree = ET.ElementTree(root)
        tree.write(path, encoding="utf-8", xml_declaration=True)

    def dumps(self):
        return ET.tostring(self.generate(), encoding="utf-8")

def main(argv=None):
    if argv is None:
        argv = sys.argv
    options = argv[1:]
    try:
        nod = NodalImage(options[0])
        if len(options) == 2:
            nod.dump(options[1])
        else:
            print(nod.dumps())
    except IndexError:
        msg = """\n Nodal to SVG\n -------------\n"""
        msg += """ Version: {0} by emcconville\n\n""".format(VERSION)
        msg += """ Copyright (c) emcconville 2016\n\n"""
        msg += """Usage:\n\n    nod2svg FILEPATH [FILEPATH]\n"""
        print(msg)

if __name__ == '__main__':
    main(sys.argv)