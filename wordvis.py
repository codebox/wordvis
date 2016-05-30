from __future__ import division
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

A correctly formatted file containing about 100,000 words can be found at:

    http://norvig.com/google-books-common-words.txt

To run the utility supply the path to the word file, and the path to the svg file as follows:

    python wordvis.py words.txt word_chart.svg


Copyright 2016 Rob Dawson

    https://github.com/codebox/wordvis
    http://codebox.org.uk/pages/word-visualiser
'''

START = '^'
END = '$'
SCALE = 1 # To produce a larger chart, but keep everything in proportion, increase this value
LINE_COLOUR = 'white'
FONT_COLOUR = '#555555'
FONT_SIZE = str(10 * SCALE) + 'px'
FONT_NAME = 'Helvetica'
COLOUR_LIGHTNESS = 0.85
MAX_RINGS = 20
RING_DEPTH = 100 * SCALE
LETTER_SPACING = 10 * SCALE

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


class Svg:
    def __init__(self, height, width):
        self.template = open('template.svg').read().replace('%height%', str(height)).replace('%width%', str(width))
        self.styles = []
        self.content = []

    def add_styles(self, selector, styles):
        styles_txt = []
        for k,v in styles.iteritems():
            styles_txt.append('{0}:{1};'.format(k,v))

        self.styles.append('{0}{{{1}}}'.format(selector,''.join(styles_txt)))

    def add_text(self, text, x, y):
        self.content.append('<text x="{0}" y="{1}">{2}</text>'.format(x, y, text))

    def add_path(self, d, clazz):
        self.content.append('<path d="{0}" class="{1}"/>'.format(d, clazz))

    def add_segment(self, letter, start_x1, start_y1, end_x1, end_y1, start_x2, start_y2, end_x2, end_y2, r1, r2):
        path = "M{0} {1} A {2} {3}, 0, 0, 1, {4} {5} L {6} {7} A {8} {9}, 0, 0, 0, {10} {11} Z".format(
            start_x1, start_y1,
            r1, r1,
            end_x1, end_y1,
            end_x2, end_y2,
            r2, r2,
            start_x2, start_y2
        )
        self.add_path(path, letter)

    def save(self, out_file):
        part1, tmp = self.template.split('%style%')
        part2, part3 = tmp.split('%substance%')

        f=open(out_file, 'w')
        f.write(part1)
        for style in self.styles:
            f.write(style)
        f.write(part2)
        for content in self.content:
            f.write(content)
        f.write(part3)
        f.close()


class CircleDiagram:
    def __init__(self, svg):
        self.ring_count = 0
        self.svg = svg
        self.center = (size/2, size/2)
        self.last_letter_pos = (0,0)

        for letter in 'abcdefghijklmnopqrstuvwxyz':
            svg.add_styles('.' + letter, {'fill' : self._colour_for_letter(letter), 'stroke' : LINE_COLOUR})

        svg.add_styles('text', {'fill':FONT_COLOUR, 'font-family' : FONT_NAME, 'font-size' : FONT_SIZE})

    def _colour_for_letter(self, letter):
        rgb = colorsys.hls_to_rgb((ord(letter) - ord('a')) / 26, COLOUR_LIGHTNESS, 1)
        return '#' + ''.join('%02x' % i for i in map(lambda x: x * 255, rgb))

    def _calc_coords(self, r, a):
        return self.center[0] + math.sin(a) * r, self.center[1] + -math.cos(a) * r

    def _draw_segment(self, letter, level, start_angle, end_angle):
        r1 = RING_DEPTH * level
        r2 = RING_DEPTH * (level + 1)

        start_x1, start_y1 = self._calc_coords(r1, start_angle)
        start_x2, start_y2 = self._calc_coords(r2, start_angle)
        end_x1, end_y1 = self._calc_coords(r1, end_angle)
        end_x2, end_y2 = self._calc_coords(r2, end_angle)

        self.svg.add_segment(letter, start_x1, start_y1, end_x1, end_y1, start_x2, start_y2, end_x2, end_y2, r1, r2)

    def _draw_letters(self, level, all_letters):
        # Draw as many letters as we can without overlapping them.

        # Calculate cartesian co-ordinates for each letter
        letter_coords = []
        r = RING_DEPTH * (level + 0.5)
        for l in all_letters:
            letter = l[0]
            start_angle = l[1]
            end_angle = l[2]
            x, y = self._calc_coords(r, (start_angle + end_angle) / 2)
            x -= 4 * SCALE
            y += 4 * SCALE

            letter_coords.append((letter, end_angle - start_angle, x, y))

        # Sort letter coordinates by size of the associated segment (largest first)
        letter_coords.sort(key=lambda n: n[1], reverse=True)
        occupied = []

        def is_room(x,y):
            for o in occupied:
                ox, oy = o
                if ((ox-x)**2 + (oy-y)**2) < LETTER_SPACING**2:
                    return False
            return True

        # O(n^2) performance blackspot here, but still runs fine for largest inputs so leaving
        for values in letter_coords:
            letter, _, x, y = values
            if is_room(x, y):
                self.svg.add_text(letter.upper(), x, y)
                occupied.append((x,y))


    def add_ring(self, parts):
        level = self.ring_count

        # Draw all the segments first
        all_letters = []
        for p in parts:
            letter = p[0]
            start_angle = p[2] * math.pi * 2
            end_angle = (p[2] + p[1]) * math.pi * 2

            all_letters.append((letter, start_angle, end_angle))

            self._draw_segment(letter, level+1, start_angle, end_angle)

        # Draw letters on top of segments so we can read them
        self._draw_letters(level+1, all_letters)

        self.ring_count += 1

    def save(self, svg_file):
        self.svg.save(svg_file)


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

size = MAX_RINGS * RING_DEPTH * 2
svg = Svg(size, size)
diagram = CircleDiagram(svg)

rings = Rings(tree)
for ring in rings.get():
    diagram.add_ring(ring)

diagram.save(svg_file)
