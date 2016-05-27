from __future__ import division
import svgwrite

START = '^'
END   = '$'

class Node:
    def __init__(self, letter):
        self.letter = letter
        self.count = 0
        self.children = {}

    def add_child(self, letter):
        self.children.put()

class EndNode:
    def __init__(self):
        self.letter = END
        self.count = 1
        self.children = {}

class Tree:
    def __init__(self):
        self.root = Node(START)

    def add(self, word):
        def add_chars(parent_node, chars):
            parent_node.count += 1
            if len(chars) == 0:
                parent_node.children[END] = EndNode()
                return

            first_letter = chars[0]
            if not parent_node.children.has_key(first_letter):
                parent_node.children[first_letter] = Node(first_letter)

            add_chars(parent_node.children[first_letter], chars[1:])

        add_chars(self.root, word)

    def __str__(self):
        lines = []
        INDENT = '  '

        def str_node(node, i):
            lines.append(i * INDENT + node.letter + ':' + str(node.count))
            for c in node.children.values():
                str_node(c, i+1)

        str_node(self.root, 0)
        return '\n'.join(lines)

tree = Tree()
for line in open('words.txt').readlines():
    tree.add(line.lower().strip())

tiers = {}

def on_node(node, depth, size, offset):
    if isinstance(node, EndNode):
        return
    if not tiers.has_key(depth):
        tiers[depth] = []
    tiers[depth].append([node.letter,size, offset])

def dfs(node, depth, node_size, offset):
    node_count = node.count
    o=offset
    for child in node.children.values():
        s = node_size * child.count/node_count
        dfs(child, depth + 1, s, o)
        o += s

    on_node(node, depth, node_size, offset)

class Diagram:
    def __init__(self):
        self.bar_height = 20
        self.bar_width  = 20000
        self.bar_count  = 0
        self.text_height = 10
        self.dwg = svgwrite.Drawing('test.svg', profile='tiny', size=(self.bar_width, self.bar_height * 10))

    def box(self, letter, x1, x2, y1, y2):
        d=self.dwg
        d.add(d.line((x1, y1), (x1, y2), stroke=svgwrite.rgb(10, 10, 16, '%')))
        d.add(d.line((x1, y2), (x2, y2), stroke=svgwrite.rgb(10, 10, 16, '%')))
        d.add(d.line((x2, y2), (x2, y1), stroke=svgwrite.rgb(10, 10, 16, '%')))
        d.add(d.line((x2, y1), (x1, y1), stroke=svgwrite.rgb(10, 10, 16, '%')))
        d.add(d.text(letter, insert=((x1+x2)/2 - 2, (y1+y2)/2 + 2), font_size = "10px"))

    def add_bar(self, parts):
        for p in parts:
            offset = p[2]
            width  = p[1]
            letter = p[0]
            self.box(letter, offset * self.bar_width, (offset+width) * self.bar_width, self.bar_count * self.bar_height, (self.bar_count +1 ) * self.bar_height)

        self.bar_count += 1

    def save(self):
        self.dwg.save()

diagram = Diagram()

dfs(tree.root, 0, 1, 0)
tier_i=0
while tiers.has_key(tier_i):
    diagram.add_bar(tiers[tier_i])
    tier_i += 1
diagram.save()