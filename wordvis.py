from __future__ import division
import svgwrite
import math
import colorsys
import sys

'''
Word Visualiser
---------------

This utility reads a text file containing word frequency data, and generates a Sunburst Chart illustrating the frequency
with which letters appear at each position within the words.

Each line of the input file must contain a single word, followed by a tab character, followed by a numeric value.
For example:

THE	53097401461
OF	30966074232
AND	22632024504
TO	19347398077

To run the utility supply the path to the word file, and the path to the svg file as follows:

    python wordvis.py words.txt word_chart.svg


Copyright 2016 Rob Dawson

    https://github.com/codebox/wordvis
    http://codebox.org.uk/pages/word-visualiser
'''

START = '^'
END = '$'
LINE_COLOUR = 'white'
FONT_COLOUR = '#555555'
FONT_SIZE = '10px'
FONT_NAME = 'Arial'
COLOUR_LIGHTNESS = 0.85
MAX_RINGS = 12
RING_DEPTH = 100
LETTER_SPACING = 0.05   # smaller values will result in more letters on the chart


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
            if first_letter not in parent_node.children:
                parent_node.children[first_letter] = Node(first_letter)

            add_chars(parent_node.children[first_letter], chars[1:], count)

        add_chars(self.root, word, count)


class CircleDiagram:
    def __init__(self, svg_file):
        self.ring_count = 0
        size = MAX_RINGS * RING_DEPTH * 2
        self.dwg = svgwrite.Drawing(svg_file, profile='tiny', size=(size, size))
        self.center = (size/2, size/2)

    def _colour_for_letter(self, letter):
        rgb = colorsys.hls_to_rgb((ord(letter) - ord('a')) / 26, COLOUR_LIGHTNESS, 1)
        return '#' + ''.join('%02x' % i for i in map(lambda x: x * 255, rgb))

    def _calc_coords(self, r, a):
        return self.center[0] + math.sin(a) * r, self.center[1] + -math.cos(a) * r

    def _draw_segment(self, letter, level, start_angle, end_angle):
        d = self.dwg

        r1 = RING_DEPTH * level
        r2 = RING_DEPTH * (level + 1)

        start_x1, start_y1 = self._calc_coords(r1, start_angle)
        start_x2, start_y2 = self._calc_coords(r2, start_angle)
        end_x1, end_y1 = self._calc_coords(r1, end_angle)
        end_x2, end_y2 = self._calc_coords(r2, end_angle)

        d.add(d.path(d="M{0} {1} A {2} {3}, 0, 0, 1, {4} {5} L {6} {7} A {8} {9}, 0, 0, 0, {10} {11} Z".format(
                start_x1, start_y1,
                r1, r1,
                end_x1, end_y1,
                end_x2, end_y2,
                r2, r2,
                start_x2, start_y2
            ), fill=self._colour_for_letter(letter), stroke=LINE_COLOUR))

    def _draw_letter(self, letter, level, start_angle, end_angle):
        d = self.dwg

        r1 = RING_DEPTH * level
        r2 = RING_DEPTH * (level + 1)

        letter_x, letter_y = self._calc_coords((r1 + r2) / 2, (start_angle + end_angle) / 2)
        d.add(d.text(letter.upper(), insert=(letter_x-2, letter_y+3),
                     font_size=FONT_SIZE, fill=FONT_COLOUR, font_family=FONT_NAME))

    def add_ring(self, parts):
        level = self.ring_count

        # Draw all the segments first
        for p in parts:
            letter = p[0]
            start_angle = p[2] * math.pi * 2
            end_angle = (p[2] + p[1]) * math.pi * 2
            self._draw_segment(letter, level+1, start_angle, end_angle)

        # Draw letters on top of segments so we can read them
        for p in parts:
            letter = p[0]
            start_angle = p[2] * math.pi * 2
            end_angle = (p[2] + p[1]) * math.pi * 2
            if (end_angle - start_angle) * (level+1) > LETTER_SPACING:
                self._draw_letter(letter, level+1, start_angle, end_angle)

        self.ring_count += 1

    def save(self):
        self.dwg.save()


class Rings:
    def __init__(self, tree):
        self.tiers = {}
        self._dfs(tree.root, 0, 1, 0)

    def _on_node(self, node, depth, size, offset):
        if isinstance(node, EndNode):
            return

        if depth not in self.tiers:
            self.tiers[depth] = []

        self.tiers[depth].append([node.letter, size, offset])

    def _dfs(self, node, depth, node_size, offset):
        node_count = node.count
        child_offset = offset

        for key in sorted(node.children.keys()):
            child = node.children[key]
            child_size = node_size * child.count/node_count
            self._dfs(child, depth + 1, child_size, child_offset)
            child_offset += child_size

        self._on_node(node, depth, node_size, offset)

    def get(self):
        return self.tiers.values()[1:]

args = sys.argv
if len(args) != 3:
    print "Usage: python {0} <word file> <svg file>".format(args[0])
    sys.exit(1)

word_file = args[1]
svg_file = args[2]

tree = Tree()
for line in open(word_file).readlines():
    word, count = line.split('\t')
    tree.add(word.lower().strip(), int(count))

rings = Rings(tree)
diagram = CircleDiagram(svg_file)

for ring in rings.get():
    diagram.add_ring(ring)

diagram.save()
