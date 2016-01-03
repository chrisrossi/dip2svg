from functools import partial
from itertools import chain, takewhile
from math import sqrt

from .svg import circle, g, line, path, svg, text
from .utils import first

DOT_R = 0.8
JUNCTION_R = 0.6
WIDTH = 0.25
FONTSIZE = 2.2
SCALE = 4


def convert(doc, sheetnum=1):
    library = Library(doc)
    schematic = doc.find('schematicDesign')
    sheets = schematic.findall('sheet')
    sheet = first((sheet for sheet in sheets
                   if sheetnumber(sheet) == sheetnum))

    width, height = schematic.find('schDesignHeader').find('workspaceSize')
    width *= SCALE
    height *= SCALE

    symbols = map(partial(draw_symbol, library), sheet.findall('symbol'))
    wires = map(draw_wire, sheet.findall('wire'))
    junctions = map(draw_junction, sheet.findall('junction'))
    ports = map(draw_port, sheet.findall('port'))
    return svg(width, height)(
        g(transform='translate(0, {})'.format(height / 2))(
            g(transform='scale({0}, {0})'.format(SCALE))(
                g('schematic', stroke='black', fill='none',
                  transform='scale(1, -1)')(
                    *chain(symbols, wires, junctions, ports)
                )
            )
        )
    )


def draw_symbol(library, node):
    refdes = node.get('refDesRef')
    x, y = node.find('pt')
    symbol = library.symbols[node.get('symbolRef')]
    container = g(refdes, transform='translate({}, {})'.format(x, y))(
        *map(partial(draw_shape, library, node), shapes(symbol))
    )
    for draw in (draw_refdes, draw_value,):
        drawing = draw(library, node, symbol)
        if drawing:
            container(drawing)
    return container


def shapes(symbol):
    return (x for x in symbol
            if getattr(x, 'name', None)
            in ('line', 'triplePointArc', 'pin', 'text'))


def draw_shape(library, symbol, shape):
    if shape.name == 'line':
        return draw_line(shape)
    elif shape.name == 'triplePointArc':
        return draw_arc(shape)
    elif shape.name == 'pin':
        return draw_pin(shape)
    elif shape.name == 'text':
        return draw_text(library, shape)


def draw_line(node):
    (x1, y1), (x2, y2) = node.findall('pt')
    width = node.get('width')
    return line(x1, y1, x2, y2, max(width, WIDTH))


def draw_arc(node):
    center, start, end = node.findall('pt')
    r = sqrt(abs(center[0] - end[0])**2 + abs(center[1] - end[1])**2)
    width = node.get('width')
    return path('M {},{} A {} {} 0 0 1 {},{}'.format(
        start[0], start[1], r, r, end[0], end[1]), width)


def draw_pin(node):
    x1, y1 = node.find('pt')
    l = node.get('pinLength')
    rotation = node.get('rotation', 0)

    container = g()
    edge_style = node.get('outsideEdgeStyle', None)
    if edge_style == 'DOT':
        # Draw a circle and then a line
        if rotation == 0:
            dot = circle(x1 + DOT_R, y1, DOT_R, WIDTH)
            pin = line(x1 + 2 * DOT_R, y1, x1 + l, y1, WIDTH)
        elif rotation == 90:
            dot = circle(x1, y1 + DOT_R, DOT_R, WIDTH)
            pin = line(x1, y1 + 2 * DOT_R, x1, y1 + l, WIDTH)
        elif rotation == 180:
            dot = circle(x1 - DOT_R, y1, DOT_R, WIDTH)
            pin = line(x1 - 2 * DOT_R, y1, x1 - l, y1, WIDTH)
        elif rotation == 270:
            dot = circle(x1, y1 - DOT_R, DOT_R, WIDTH)
            pin = line(x1, y1 - 2 * DOT_R, x1, y1 - l, WIDTH)
        container(dot, pin)

    else:
        # No dot, just draw the line
        if rotation == 0:
            x2, y2 = x1 + l, y1
        elif rotation == 90:
            x2, y2 = x1, y1 + l
        elif rotation == 180:
            x2, y2 = x1 - l, y1
        elif rotation == 270:
            x2, y2 = x1, y1 - l
        container(line(x1, y1, x2, y2, WIDTH))

    display = node.find('pinDisplay')
    if display and display.get('dispPinName'):
        tx = WIDTH * 2
        tx = -tx if rotation == 0 else tx
        anchor = 'end' if rotation == 0 else 'start'
        container(
            g(transform='translate({}, {})'.format(x1 + tx, y1))(
                g(transform='scale(1, -1)')(
                    text(0, 0, FONTSIZE, **{
                        'text-anchor': anchor,
                        'style': 'dominant-baseline: central;',
                    })(node.get('defaultPinDes'))
                )
            )
        )

    return container


def draw_text(library, node):
    x, y = node.find('pt')
    anchor = 'middle' if node.get('justify', None) == 'Center' else 'start'
    style = library.text_styles[node.get('textStyleRef')]
    fontsize = style.find('font').get('fontHeight')
    return g(transform='translate({}, {})'.format(x, y - fontsize / 2))(
        g(transform='scale(1, -1)')(
            text(0, 0, fontsize, **{'text-anchor': anchor})(node[1])
        )
    )


def find_attr(node, type):
    return first((attr for attr in node.findall('attr') if attr[0] == type))


def draw_refdes(library, symbol, ref):
    attr = find_attr(ref, 'RefDes')
    if not attr:
        return

    if not attr.get('isVisible'):
        return

    override = find_attr(symbol, 'RefDes')
    if override and not override.get('isVisible'):
        return

    x, y = attr.find('pt')
    refdes = symbol.get('refDesRef').replace('_', '.')
    rotate = (refdes_prefix(refdes) in ('R', 'D', 'U', 'C',) and
              all((pin.get('rotation', 0) in (90, 270)
                   for pin in ref.findall('pin'))))
    if rotate and refdes_prefix(refdes) in ('R', 'D'):
        y = y / 2
    style = library.text_styles[attr.get('textStyleRef')]
    fontsize = style.find('font').get('fontHeight')

    drawing = g(transform='translate({}, {})'.format(x, y))(
        g(transform='scale(1, -1)')(
            text(0, 0, fontsize)(refdes)
        )
    )

    if (rotate):
        drawing = g(transform='rotate(90)')(drawing)

    return drawing


def refdes_prefix(refdes):
    return ''.join(takewhile(lambda ch: not ch.isdigit(), refdes))


def draw_value(library, symbol, ref):
    attr = find_attr(ref, 'RefDes')
    if not attr:
        return

    refdes = symbol.get('refDesRef').replace('_', '.')
    if refdes_prefix(refdes) not in ('R', 'C'):
        return

    value = library.components[refdes].get('compValue')
    if not value:
        return

    x, y = attr.find('pt')
    rotate = all((pin.get('rotation', 0) in (90, 270)
                  for pin in ref.findall('pin')))
    if rotate and refdes_prefix(refdes) == 'R':
        y = y / 2
    style = library.text_styles[attr.get('textStyleRef')]
    fontsize = style.find('font').get('fontHeight')

    drawing = g(transform='translate({}, {})'.format(x, -y))(
        g(transform='scale(1, -1)')(
            text(0, 0, fontsize, style='dominant-baseline: text-before-edge')(
                value
            )
        )
    )

    if (rotate):
        drawing = g(transform='rotate(90)')(drawing)

    return drawing


def draw_wire(node):
    return draw_line(node.find('line'))


def draw_junction(node):
    x, y = node.find('pt')
    return g(fill='black')(circle(x, y, JUNCTION_R, WIDTH))


def draw_port(node):
    l = 1  # Length of arrow's 'shaft'
    barb_l, barb_h = 1, 0.8  # Length, height of arrow's 'barbs'
    x, y = node.find('pt')
    rotation = node.get('rotation', 0)
    if rotation == 0:
        return g()(
            line(x, y, x + l, y, WIDTH),
            line(x + l, y, x + l - barb_l, y + barb_h, WIDTH),
            line(x + l, y, x + l - barb_l, y - barb_h, WIDTH),
            g(transform='translate({}, {})'.format(x + l + 2 * WIDTH, y))(
                g(transform='scale(1, -1)')(
                    text(0, 0, FONTSIZE * 0.9,
                         style='dominant-baseline: middle')(
                        node.get('netNameRef')
                    )
                )
            )
        )
    elif rotation == 180:
        return g()(
            line(x, y, x - l, y, WIDTH),
            line(x - l, y, x - l + barb_l, y + barb_h, WIDTH),
            line(x - l, y, x - l + barb_l, y - barb_h, WIDTH),
            g(transform='translate({}, {})'.format(x - l - 2 * WIDTH, y))(
                g(transform='scale(1, -1)')(
                    text(0, 0, FONTSIZE * 0.9,
                         style='dominant-baseline: middle', **{
                             'text-anchor': 'end',
                         })(
                        node.get('netNameRef')
                    )
                )
            )
        )
    elif rotation == 90:
        return g()(
            line(x, y, x, y + l, WIDTH),
            line(x, y + l, x + barb_h, y + l - barb_l, WIDTH),
            line(x, y + l, x - barb_h, y + l - barb_l, WIDTH),
            g(transform='translate({}, {})'.format(x, y + l + 2 * WIDTH))(
                g(transform='scale(1, -1)')(
                    text(0, 0, FONTSIZE * 0.9, **{'text-anchor': 'middle',})(
                        node.get('netNameRef')
                    )
                )
            )
        )
    elif rotation == 270:
        return g()(
            line(x, y, x, y - l, WIDTH),
            line(x, y - l, x + barb_h, y - l + barb_l, WIDTH),
            line(x, y - l, x - barb_h, y - l + barb_l, WIDTH),
            g(transform='translate({}, {})'.format(x, y - l - 2 * WIDTH))(
                g(transform='scale(1, -1)')(
                    text(0, 0, FONTSIZE * 0.9,
                         style='dominant-baseline: text-before-edge', **{
                             'text-anchor': 'middle',
                         })(
                        node.get('netNameRef')
                    )
                )
            )
        )


def sheetnumber(sheet):
    return sheet.get('sheetNum')


class Library(object):

    def __init__(self, doc):
        lib = doc.find('library')
        self.text_styles = {x[0]: x for x in lib.findall('textStyleDef')}
        self.symbols = {x[0]: x for x in lib.findall('symbolDef')}

        netlist = doc.find('netlist')
        self.components = {x[0]: x for x in netlist.findall('compInst')}
