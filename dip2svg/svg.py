from kemmer import tag


def svg(width, height):
    return tag('svg',
        x='0',
        y='0',
        width=width,
        height=height,
        viewBox='0 0 {} {}'.format(width, height),
        xmlns='http://www.w3.org/2000/svg',
        version='1.1',
        **{'xmlns:svg': 'http://www.w3.org/2000/svg'}
    )


def g(id=None, **kw):
    if id:
        kw['id'] = id
    return tag('g', **kw)


def line(x1, y1, x2, y2):
    return tag('line', x1=x1, y1=y1, x2=x2, y2=y2)


def path(d):
    return tag('path', d=d)


def circle(x, y, r):
    return tag('circle', cx=x, cy=y, r=r)


def text(x, y, **kw):
    return tag('text', x=x, y=y, **kw)
