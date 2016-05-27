from __future__ import division
import svgwrite
import math

START = '^'
END   = '$'

class Node:
    def __init__(self, letter):
        self.letter = letter
        self.count = 0
        self.children = {}

class EndNode:
    def __init__(self):
        self.letter = END
        self.count = 1
        self.children = {}

class Tree:
    def __init__(self):
        self.root = Node(START)

    def add(self, word, count):
        def add_chars(parent_node, chars, count):
            parent_node.count += count
            if len(chars) == 0:
                parent_node.children[END] = EndNode()
                return

            first_letter = chars[0]
            if not parent_node.children.has_key(first_letter):
                parent_node.children[first_letter] = Node(first_letter)

            add_chars(parent_node.children[first_letter], chars[1:], count)

        add_chars(self.root, word, count)

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
    w,c = line.split('\t')
    tree.add(w.lower().strip(), int(c))

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

class CircleDiagram:
    def __init__(self):
        self.ring_depth = 100
        self.ring_count  = 0
        self.text_height = 10
        MAX_RINGS = 20
        PADDING = 100
        size = (MAX_RINGS * self.ring_depth + PADDING) * 2
        self.dwg = svgwrite.Drawing('test.svg', profile='tiny', size=(size, size))
        self.center = (size/2, size/2)

    def calc_coords(self, r, a):
        return (self.center[0] + math.sin(a) * r, self.center[1] + -math.cos(a) * r)

    def draw_segment(self, letter, level, start_angle, end_angle):
        d=self.dwg

        r1 = self.ring_depth * level
        r2 = self.ring_depth * (level + 1)

        start_x1, start_y1 = self.calc_coords(r1, start_angle)
        start_x2, start_y2 = self.calc_coords(r2, start_angle)
        d.add(d.line((start_x1, start_y1), (start_x2, start_y2), stroke='black'))

        end_x1, end_y1 = self.calc_coords(r1, end_angle)
        end_x2, end_y2 = self.calc_coords(r2, end_angle)
        d.add(d.line((end_x1, end_y1), (end_x2, end_y2), stroke='black'))

        letter_x, letter_y = self.calc_coords((r1 + r2) / 2, (start_angle + end_angle) / 2)
        d.add(d.text(letter, insert=(letter_x+2, letter_y+2), font_size = "10px"))

    def draw_ring(self, level):
        d=self.dwg
        d.add(d.circle(center=self.center, r = self.ring_depth * level, stroke='black', fill='none'))

    def add_ring(self, parts):
        level = self.ring_count
        self.draw_ring(level)

        for p in parts:
            letter      = p[0]
            start_angle = p[2] * math.pi * 2
            end_angle   = (p[2] + p[1]) * math.pi * 2
            self.draw_segment(letter, level, start_angle, end_angle)

        self.ring_count += 1

    def save(self):
        self.dwg.save()

diagram = CircleDiagram()

dfs(tree.root, 0, 1, 0)
tier_i=0
while tiers.has_key(tier_i):
    diagram.add_ring(tiers[tier_i])
    tier_i += 1
diagram.save()