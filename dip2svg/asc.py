"""
Parse DipTrace ascii files.
"""
from collections import deque

from .utils import first

_nodefault = object()


class List(list):
    """
    Basic lisp-like list primitive that seems to be the basis of the DipTrace
    ascii format.
    """
    def __init__(self, name, items):
        self.name = name
        super(List, self).__init__(items)

    def __repr__(self):
        return '{}({}, {})'.format(
            type(self).__name__,
            self.name,
            super(List, self).__repr__(),
        )

    def find(self, name, descendents=False):
        return first(self.findall(name, descendents))

    def findall(self, name, descendents=False):
        items = breadthfirst(self) if descendents else self
        for item in (x for x in items if isinstance(x, List)):
            if item.name == name:
                yield item

    def get(self, name, default=_nodefault):
        node = self.find(name)
        if not node:
            if default is not _nodefault:
                return default
            raise KeyError(name)
        if len(node) != 1:
            raise ValueError(node)
        return node[0]


def parse(f):
    return List(None, list(_parse_items(f)))


def depthfirst(n):
    if isinstance(n, List):
        for child in n:
            for desc in depthfirst(child):
                yield desc
    yield n


def breadthfirst(root):
    Q = deque()
    Q.append(root)

    while Q:
        node = Q.popleft()
        yield node

        if isinstance(node, List):
            Q.extend(node.items)


def _parse_items(f):
    ch = f.read(1)
    while True:
        while ch.isspace():
            ch = f.read(1)

        if ch == '"':
            ch, token = _token(f, lambda ch: ch == '"')
            yield token
            ch = f.read(1)

        elif ch == '(':
            yield _parse_list(f)
            ch = f.read(1)

        elif ch == ')':
            break

        elif not ch:
            break

        else:
            ch, n = _parse_token(ch, f)
            yield n


def _parse_string(f):
    b = bytearray()
    ch = f.read(1)
    while ch != '"':
        b.append(ch)
        ch = f.read(1)
    return str(b)


def _parse_list(f):
    ch, name = _token(f, lambda ch: ch.isspace() or ch == ')')
    items = () if ch == ')' else list(_parse_items(f))
    return List(name, items)


def _token(f, until, pre=None):
    b = bytearray()
    if pre:
        b.append(pre)
    ch = f.read(1)
    while not until(ch):
        b.append(ch)
        ch = f.read(1)
    return ch, str(b)


def _parse_token(ch, f):
    ch, token = _token(f, lambda ch: ch.isspace() or ch == ')', ch)
    if token.endswith('%'):
        return ch, Percent(token[:-1])
    for converter in (int, float, asbool, Token):
        try:
            token = converter(token)
            break
        except ValueError:
            continue

    return ch, token


class Percent(float):
    pass


class Token(str):
    pass


def asbool(x):
    if x == 'True':
        return True
    elif x == 'False':
        return False
    raise ValueError(x)
