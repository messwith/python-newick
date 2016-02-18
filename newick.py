# coding: utf8
from __future__ import unicode_literals
import io


RESERVED_PUNCTUATION = ':;,()'


class Node(object):
    def __init__(self, name=None, length=None, descendants=None):
        for char in RESERVED_PUNCTUATION:
            if (name and char in name) or (length and char in length):
                raise ValueError(
                    'Node names or branch lengths must not contain "%s"' % char)
        self.name = name
        self.length = length
        self.descendants = descendants or []

    @property
    def newick(self):
        label = self.name or ''
        if self.length:
            label += ':' + self.length
        descendants = ','.join([n.newick for n in self.descendants])
        if descendants:
            descendants = '(' + descendants + ')'
        return descendants + label

    @property
    def is_leaf(self):
        return not bool(self.descendants)

    def walk(self, mode=None):
        if mode == 'postorder':
            for n in self._postorder():
                yield n
        else:  # default to a breadth-first search
            yield self
            for node in self.descendants:
                for n in node.walk():
                    yield n

    def _postorder(self):
        stack = [self]
        descendant_map = {id(node): [n for n in node.descendants] for node in self.walk()}

        while stack:
            node = stack[-1]
            descendants = descendant_map[id(node)]

            # if we are at a leave-node, we remove the item from the stack
            if not descendants:
                stack.pop()
                yield node
                if stack:
                    descendant_map[id(stack[-1])].pop(0)
            else:
                stack.append(descendants[0])


def loads(s):
    return [parse_node(ss.strip()) for ss in s.split(';') if ss.strip()]


def dumps(trees):
    if isinstance(trees, Node):
        trees = [trees]
    return ';\n'.join([tree.newick for tree in trees]) + ';'


def load(fp):
    return loads(fp.read())


def dump(tree, fp):
    fp.write(dumps(tree))


def read(fname, encoding='utf8'):
    with io.open(fname, encoding=encoding) as fp:
        return load(fp)


def write(tree, fname, encoding='utf8'):
    with io.open(fname, encoding=encoding, mode='w') as fp:
        dump(tree, fp)


def _parse_name_and_length(s):
    l = None
    if ':' in s:
        s, l = s.split(':', 1)
    return s or None, l or None


def _parse_siblings(s):
    """
    http://stackoverflow.com/a/26809037
    """
    bracket_level = 0
    current = []

    # trick to remove special-case of trailing chars
    for c in (s + ","):
        if c == "," and bracket_level == 0:
            yield parse_node("".join(current))
            current = []
        else:
            if c == "(":
                bracket_level += 1
            elif c == ")":
                bracket_level -= 1
            current.append(c)


def parse_node(s):
    s = s.strip()
    parts = s.split(')')
    if len(parts) == 1:
        descendants, label = [], s
    else:
        if not parts[0].startswith('('):
            raise ValueError('unmatched braces %s' % parts[0][:100])
        descendants, label = list(_parse_siblings(')'.join(parts[:-1])[1:])), parts[-1]
    name, length = _parse_name_and_length(label)
    return Node(name=name, length=length, descendants=descendants)