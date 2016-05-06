""":mod:`nod2svg.main` --- NodalImage object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Opens Nodal document and builds a SVG image::

    NodalImage(path_to_nod).dump(path_to_svg)

"""
import math
import plistlib
import xml.etree.cElementTree as ET

from .constants import *

all = ('NodalImage',
       'NodalException',
       'VERSION',
       'main')

VERSION = '0.1.2'


class NodalException(Exception):
    """
    Generic exception namespace.

    .. versionadded:: 0.1.2
    """
    pass


class NodalImage(object):
    """
    A primary class for parsing Nodal documents, and generating an SVG image.

    Write an SVG image::

        from nod2svg.main import NodalImage

        NodalImage(path_to_nod).dump(path_to_svg)

    Generating an SVG string::

        from nod2svg.main import NodalImage

        svg_string = NodalImage(path_to_nod).dumps()

    Generate a SVG DOM tree::

        from nod2svg.main import NodalImage

        svg_dom_root = NodalImage(path_to_nod).generate()

    .. versionadded:: 0.1.0
    """
    VERSION = VERSION
    elements = {}
    edges = {}
    nodes = {}
    textboxes = {}
    bg = 'transparent'
    ec = '#717589ff'
    nc = '#9b9effff'
    ac = '#ffffff80'
    title = None
    author = None
    comment = None

    mbr = [99999999999999,
           99999999999999,
           -99999999999999,
           -99999999999999]

    @property
    def background_color(self):
        """(:class:`basestring`)
        The hexadecimal value of the background color
        .. versionadded:: 0.1.0
        """
        return self.bg[:7]

    @property
    def background_opacity_color(self):
        """(:class:`basestring`)
        The percent value of the background opacity
        .. versionadded:: 0.1.0
        """
        return STRING_FLOAT_FORMAT.format(int(self.bg[-2:], 16) / 256.0)

    @property
    def node_color(self):
        """(:class:`basestring`)
        The hexadecimal value of the Node color
        .. versionadded:: 0.1.0
        """
        return self.nc[:7]

    @property
    def node_opacity_color(self):
        """(:class:`basestring`)
        The percent value of the Node opacity
        .. versionadded:: 0.1.0
        """
        return STRING_FLOAT_FORMAT.format(int(self.nc[-2:], 16) / 256.0)

    @property
    def node_fill_color(self):
        """(:class:`basestring`)
        The hexadecimal value of the Node color.

        .. seealso::
            Alias of :meth:`node_color`

        .. versionadded:: 0.1.0
        """
        return self.node_color

    @property
    def node_fill_opacity_color(self):
        """(:class:`basestring`)
        The percent value of the Node fill opacity.
        Defaults to 16% of given alpha.

        .. versionadded:: 0.1.0
        """
        given_alpha = int(self.nc[-2:], 16) / 256.0
        return STRING_FLOAT_FORMAT.format(given_alpha * 0.16)

    @property
    def edge_color(self):
        """(:class:`basestring`)
        The hexadecimal value of the Edge color"""
        return self.ec[:7]

    @property
    def edge_opacity_color(self):
        """(:class:`basestring`)
        The percent value of the Edge opacity.

        .. versionadded:: 0.1.0
        """
        return STRING_FLOAT_FORMAT.format(int(self.ec[-2:], 16) / 256.0)

    @property
    def annotation_color(self):
        """(:class:`basestring`)
        The hexadecimal value of the Annotation color

        .. versionadded:: 0.1.0
        """
        return self.ac[:7]

    @property
    def annotation_opacity_color(self):
        """(:class:`basestring`)
        The percent value of the Annotation opacity."""
        return STRING_FLOAT_FORMAT.format(int(self.ac[-2:], 16) / 256.0)

    def __init__(self, path=None):
        """
        Initialize NodalImage instance.

        Will load Nodal document if ``path`` argument is given.

        :param path: Optional path of Nodal. Default=``None``
        :type path: :class:`basestring`

        .. versionadded:: 0.1.0
        """
        if path:
            self.load(path)

    def dump(self, path):
        """
        Generates and writes an SVG document to a system path.

        :param path: The system path to write an SVG to.
        :type path: :class:`basestring`

        .. versionadded:: 0.1.0
        """
        root = self.generate()
        tree = ET.ElementTree(root)
        tree.write(path, encoding="utf-8", xml_declaration=True)

    def dumps(self):
        """
        Generates and returns an SVG document.

        :rtype: :class:`basestring`

        .. versionadded:: 0.1.0
        """
        return ET.tostring(self.generate(), encoding="utf-8")

    def load(self, path):
        """
        Read Nodal document from system path.

        Loads meta-data, style, and element properties.

        :param path: The path to a Nodal document.
        :type path: :class:`basestring`
        :raises: :class:`NodalException`

        .. versionadded:: 0.1.0
        """
        with open(path, 'rb') as fd:
            nod = plistlib.readPlist(fd)
            if ELEMENTS not in nod:
                raise NodalException('Not a Nodal matrix')
            self.elements = nod[ELEMENTS]
            if AUTHOR in nod:
                self.author = nod[AUTHOR]
            if TITLE in nod:
                self.title = nod[TITLE]
            if COMMENT in nod:
                self.comment = nod[COMMENT]
            if STYLE_BACKGROUND_COLOR in nod:
                self.bg = nod[STYLE_BACKGROUND_COLOR]
            if STYLE_ANNOTATION_COLOR in nod:
                self.ac = nod[STYLE_ANNOTATION_COLOR]
        self.nodes = self.lookup(TYPE, NODE)
        self.edges = self.lookup(TYPE, EDGE)
        self.textboxes = self.lookup(TYPE, TEXTBOX)

    def lookup(self, attr, val):
        """
        Iterate over all elements and return a dictionary with matching
        scope (``attr``) & value (``val``)

        If element has key :const:`nod2svg.constants.TICKPOS` then parse tick
        position, grow minimum bounding rectangle, and index coordinates.

        :param attr: The directory key to scan for.
        :type attr: :class:`basestring`
        :param val: The value to filter by.
        :type val: :class:`basestring`

        .. versionadded:: 0.1.0
        .. versionchanged:: 0.1.1
           Generate DOM ID attributes for all elements.
        """
        matches = {}
        for key in self.elements:
            node = self.elements[key]
            if attr in node and node[attr] == val:
                # Generate DOM ID for future reference.
                node[DOM_ID] = ID_FORMAT.format(val, len(matches))
                if TICKPOS in node:
                    x, y = self.parse_tick_position(node[TICKPOS])
                    node[X], node[Y] = self.grow_minimum_bounding_rectangle(x,
                                                                            y)
                matches[key] = node
        return matches

    def parse_tick_position(self, attr):
        """
        Convert Nodal coordinate string into tuple.

        for example::

            "{x y}" => ("x", "y")

        :param attr: The Nodal coordinate string.
        :type attr: :class:`basestring`
        :rtype: :class:`tuple`

        .. versionadded:: 0.1.0
        """
        attr = attr.lstrip('{').rstrip('}')
        return attr.split(', ')

    def grow_minimum_bounding_rectangle(self, x, y):
        """
        Increases the size of the Minimum Bounding Rectangle, and returns
        the original given values as :class:`numbers.Integral`.

        :param x: X coordinate of point.
        :type x: :class:`basestring`
        :param y: Y coordinate of point.
        :type y: :class:`basestring`
        :rtype: :class:`tuple`

        .. versionadded:: 0.1.0
        """
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

    def generate_nodes(self, root):
        """
        Iterate over all Nodes from element structure, and
        generate an SVG ``'circle'`` element.

        Additional glyphs will be appended by xlink reference if the Node
        has been flagged as Parallel or Random attributes.

        .. versionadded:: 0.1.0
        .. versionchanged:: 0.1.1
            Mouseover events now build Node elements and connected
            Edge elements.
        """
        group = ET.SubElement(root, 'g')
        n = self.nodes
        for k in n:
            v = n[k]
            dot_attr = {'cx': '{0}'.format(v[X]),
                        'cy': '{0}'.format(v[Y]),
                        'id': v[DOM_ID],
                        'r': '64000',
                        'fill': self.node_fill_color,
                        'fill-opacity': self.node_fill_opacity_color,
                        'stroke': self.node_color,
                        'stroke-opacity': self.node_opacity_color,
                        'stroke-width': '6400'}
            dot = ET.SubElement(group, 'circle', **dot_attr)
            sa = {'attributeName': 'stroke-width',
                  'to': '12800',
                  'begin': '{0}.mouseover'.format(v[DOM_ID]),
                  'end': '{0}.mouseout'.format(v[DOM_ID])}
            s = ET.SubElement(dot, 'set', **sa)
            if DONT_PLAY_NOTE in v and v[DONT_PLAY_NOTE]:
                dot.attrib['stroke-dasharray'] = '32000 12800'
            if v['SignallingMethod'] == 'Parallel':
                use_attr = {'xlink:href': '#parallel_head',
                            'x': '{0}'.format(v[X]),
                            'y': '{0}'.format(v[Y])}
                use = ET.SubElement(group, 'use', **use_attr)
            elif v['SignallingMethod'] == 'Random':
                use_attr = {'xlink:href': '#random_head',
                            'x': '{0}'.format(v[X]),
                            'y': '{0}'.format(v[Y])}
                use = ET.SubElement(group, 'use', **use_attr)

    def generate_edges(self, root):
        """
        Iterate over all edge elements, and build SVG paths between nodes.

        This assumes that :attr:`NodalImage.nodes` has already been populated.

        :param root: The XML root node to append grouped path elements.
        :type root: :class:`xml.etree.cElementTree.Element`

        .. versionadded:: 0.1.0
        .. versionchanged:: 0.1.1
            Each edge is now isolated within a group element,
            and includes arrow head marker and Node mouseover
            effects.
        """
        e = self.edges
        for k in e:
            v = e[k]
            start = self.nodes['{0}'.format(v[FROM_NODE])]
            end = self.nodes['{0}'.format(v[TO_NODE])]

            if EDGE_OUTS not in start:
                start[EDGE_OUTS] = []
            start[EDGE_OUTS].append(v['DOM_ID'])

            if v[PATH] == DIRECT:
                path = self.path_direct(start, end)
            elif v[PATH] == CITYBLOCK:
                path = self.path_city_block(start, end)
            elif v[PATH] == CITYBLOCKFLIPPED:
                path = self.path_city_block_flipped(start, end)
            else:
                continue
            edge_idx = len(start[EDGE_OUTS]) - 1
            edge_color = EDGE_COLORS[edge_idx % len(EDGE_COLORS)]
            g_edges = ET.SubElement(root, 'g')
            # Arrow head
            arrow_head_id = 'arrow_head_'+v['DOM_ID']
            maker_attr = {'id': arrow_head_id,
                          'orient': 'auto',
                          'markerWidth': '6',
                          'markerHeight': '6',
                          'refX': '5.0',
                          'refY': '3'}
            maker = ET.SubElement(g_edges, 'marker', **maker_attr)
            path_attr = {'d': 'M 0 0 V 6 L 6 3 Z',
                         'fill': self.edge_color,
                         'fill-opacity': self.edge_opacity_color}
            arrow_head = ET.SubElement(maker,
                                       'path',
                                       **path_attr)
            sa = {'attributeName': 'fill',
                  'to': edge_color,
                  'begin': '{0}.mouseover'.format(start[DOM_ID]),
                  'end': '{0}.mouseout'.format(start[DOM_ID])}
            s = ET.SubElement(arrow_head, 'set', **sa)
            line_attr = {'d': path,
                         'fill': 'transparent',
                         'id': v['DOM_ID'],
                         'marker-end': 'url(#{0})'.format(arrow_head_id),
                         'stroke': self.edge_color,
                         'stroke-opacity': self.edge_opacity_color,
                         'stroke-width': '6400'}
            line = ET.SubElement(g_edges, 'path', **line_attr)
            if WORMHOLE in v and v[WORMHOLE]:
                line.attrib['stroke-dasharray'] = '32000 12800'
            sa = {'attributeName': 'stroke',
                  'to': edge_color,
                  'begin': '{0}.mouseover'.format(start[DOM_ID]),
                  'end': '{0}.mouseout'.format(start[DOM_ID])}
            s = ET.SubElement(line, 'set', **sa)
            sa = {'attributeName': 'stroke-width',
                  'to': '12800',
                  'begin': '{0}.mouseover'.format(start[DOM_ID]),
                  'end': '{0}.mouseout'.format(start[DOM_ID])}
            s = ET.SubElement(line, 'set', **sa)

    def generate_text_boxes(self, root):
        """
        Iterate over all text box elements, and build SVG foreignObject
        for each text element.

        This assumes that :attr:`NodalImage.textboxes` has already been
        populated.

        :param root: The XML root node to append grouped foreignObject
                     elements.
        :type root: :class:`xml.etree.cElementTree.Element`

        .. versionadded:: 0.1.0
        """
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
            html = ET.fromstring(v[TEXT])
            #  Poorly attempt to scale text up to a level that can be viewed.
            t = 'scale(4150) translate({}, {})'.format(-v[X] * 0.999755,
                                                       -v[Y] * 0.999765)
            fobject = ET.SubElement(g_text,
                                    'foreignObject',
                                    x='{0}'.format(v[X]),
                                    y='{0}'.format(v[Y]),
                                    transform=t,
                                    **fo_attr)
            html.attrib['xmlns'] = w3_uri
            fobject.append(html)

    def generate(self):
        """
        Create SVG DOM tree, and attache groups of nodes, edges, and text
        graphics elements.

        Returns root element to determine writing/output options.

        :rtype: :class:`xml.etree.cElementTree.Element`

        .. versionadded:: 0.1.0
        .. versionchanged:: 0.1.1
            Arrow head element removed from document
            ``'refs'`` table.
        .. versionchanged:: 0.1.2
            Added title, command, and author attributes.
        """
        svg_attr = {'xmlns': 'http://www.w3.org/2000/svg',
                    'xmlns:xlink': 'http://www.w3.org/1999/xlink',
                    'version': '1.1',
                    'style': 'background:{};'.format(self.background_color)}
        svg = ET.Element('svg',
                         **svg_attr)
        defs = ET.SubElement(svg, 'defs')

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

        def safe(s):
            return s.replace('<', '&lt;').replace('>', '&gt;')
        if self.title is not None:
            ET.SubElement(svg, 'title').text = safe(self.title)
        if self.comment is not None:
            ET.SubElement(svg, 'desc').text = safe(self.comment)
        comment = ' Created with nod2svg {0} '.format(self.VERSION)
        svg.append(ET.Comment(comment))
        if self.author is not None and len(self.author) > 0:
            author = ' Nodal authored by {0} '.format(self.author)
            svg.append(ET.Comment(author))
        self.generate_text_boxes(svg)
        self.generate_edges(svg)
        self.generate_nodes(svg)
        self.mbr[0] -= GRID_TICK * 2
        self.mbr[1] -= GRID_TICK * 2
        self.mbr[2] += GRID_TICK * 2
        self.mbr[3] += GRID_TICK * 2
        t, l, w, h = self.mbr
        w = abs(t) + abs(w)
        h = abs(l) + abs(h)
        svg.attrib['viewBox'] = '{0} {1} {2} {3}'.format(t, l, w, h)
        return svg

    def path_vertical(self, start, end):
        """
        Generate vertical path data.

        :param start: Start point.
        :type start: :class:`tuple`
        :param end: End point.
        :type end: :class:`tuple`
        :rtype: :class:`basestring`

        .. versionadded:: 0.1.0
        """
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
        """
        Generate horizontal path data.

        :param start: Start point.
        :type start: :class:`tuple`
        :param end: End point.
        :type end: :class:`tuple`
        :rtype: :class:`basestring`

        .. versionadded:: 0.1.0
        """
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
        """
        Generate city block path data.

        :param start: Start point.
        :type start: :class:`tuple`
        :param end: End point.
        :type end: :class:`tuple`
        :rtype: :class:`basestring`

        .. versionadded:: 0.1.0
        """
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
        """
        Generate inverted city block path.

        :param start: Start point.
        :type start: :class:`tuple`
        :param end: End point.
        :type end: :class:`tuple`
        :rtype: :class:`basestring`

        .. versionadded:: 0.1.0
        """
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
        """
        Generate straight-line path data between two points.

        :param start: Start point.
        :type start: :class:`tuple`
        :param end: End point.
        :type end: :class:`tuple`
        :rtype: :class:`basestring`

        .. versionadded:: 0.1.0
        """
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
        return "M {0} {1} L {2} {3}".format(start_x,
                                            start_y,
                                            end_x,
                                            end_y)


def main():
    """
    Entry point for console script.

    .. versionadded:: 0.1.0
    .. versionchanged:: 0.1.2
       Simplified banner, and sent to stderr.
    """
    import sys
    options = sys.argv[1:]
    try:
        nod = NodalImage(options[0])
        if len(options) == 2:
            nod.dump(options[1])
        else:
            sys.stdout.write(nod.dumps().decode() + '\n')
    except IndexError:
        msg = ('',
               ' nod2svg {0} by emcconville',
               ' -------------------------------------',
               ' http://github.com/emcconville/nod2svg',
               '',
               ' Usage:',
               '       nod2svg FILEPATH [FILEPATH]',
               '',
               '')
        sys.stderr.write('\n'.join(msg).format(VERSION))


if __name__ == '__main__':
    main()
