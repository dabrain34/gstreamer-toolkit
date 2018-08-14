# usage :
# $ python gobj-log-2-graph.py file.log mygraph.dot
# $ dot -Tsvg mygraph.dot mygraph.svg
#
# if something:
# dot is in graphviz package
# apt install graphviz

import re
import fileinput
import sys

# 'obj' : 'parent'

g_pads = []
g_elements = []

g_bins = []
g_graph_elements = []
indent_char = '\t'

class Element:
  name = None
  bin_name = None
  class_name = None

  def __init__(self, name, bin_name = None, class_name=None):
    self.name = name
    self.bin_name = bin_name
    self.class_name = class_name

class Pad:
  name = None
  element_name = None
  peer_name = None
  pad_details = None

  def __init__(self, pad_name, peer_name = None, pad_details = None):
    self.name = pad_name
    self.element_name = pad_name.split(':')[0]
    self.peer_name = peer_name
    self.pad_details = pad_details

  def is_sink(self):
    if 'sink' in self.name:
       return True
    return False

  def is_src(self):
    if 'src' in self.name:
       return True
    return False

class Config:
    has_playbin = False
    root_bin = Element('pipeline0',None)
    extra_root_bin_comments = ''

config = Config() 

def get_element_by_name(element_name):
  for e in g_elements:
    if e.name == element_name:
      return e
  return None

def get_pad_by_name(pad_name):
  for p in g_pads:
    if p.name == pad_name:
      return p
  return None

def get_src_pad_by_element_name(el_name):
  for p in g_pads:
    if p.is_src() and p.element_name == el_name:
      return p
  return None

def new_element_in_graph (element):
  for el in g_graph_elements:
    if el.name == element.name:
      return False
  return True

def new_bin (bin_element):
  for b in g_bins:
    if b == bin_element:
      return False
  return True

def get_root_bins():
  root_bins = []
  if config.root_bin:
    root_bins.append(config.root_bin)
  for e in g_elements:
    if e.bin_name == '(NULL)':
      root_bins.append(e)
  return root_bins

def get_elements_from_bin(bin_el):
  elements = []
  for e in g_elements:
    if e.bin_name == bin_el.name:
      elements.append(e)
  return elements

def get_pad_for_element(element):
  pads = []
  for p in g_pads:
    pad = p.name.split(':')[0]
    if p.name.split(':')[0] == element.name:
      pads.append(p)
  return pads
      
def beautify_name(name):
  for r in [':', '-']:
    name = name.replace(r, '_')
  return name

def add_connection(pad_src, pad_sink, indent, label=''):
  print indent,'%s -> %s %s' %(beautify_name(pad_sink),beautify_name(pad_src), label)

def add_pad(pad, indent):
  body_indent = indent + indent;
  print indent,'subgraph ',beautify_name(pad.name),'{'
  print body_indent,'label="";'
  print body_indent,'style="invis";'
  if pad.is_sink():
    print body_indent,beautify_name(pad.name),'[color=black, fillcolor="#aaaaff", label="sink\\n[>][bfb]", height="0.2", style="filled,solid"];'
  else:
    print body_indent,beautify_name(pad.name),'[color=black, fillcolor="#aaaaff", label="src\\n[>][bfb]", height="0.2", style="filled,solid"];'
  print indent,'}'

def add_element (element, parent_bin, indent):
  if new_element_in_graph(element):
    body_indent = indent + indent;
    print indent,'subgraph cluster_%s {' % beautify_name(element.name)
    print body_indent,'fontname="Bitstream Vera Sans";'
    print body_indent,'fontsize="8";'
    print body_indent,'style="filled,rounded";'
    print body_indent,'color=black;'
    print body_indent,'label="%s\\n[>]\\nparent=(GstPipeline) %s"' % (beautify_name(element.name), parent_bin.name)
    for p in get_pad_for_element(element):
      add_pad(p, indent + indent_char)
      if p.is_src():
        add_connection(p.name, p.peer_name, indent, p.pad_details)

    for el in get_elements_from_bin(element):
      add_element(el, element, indent + indent_char)
    print indent,'fillcolor="#aaaaff";'
    print indent,'}'

#subgraph
def create_subgraph(indent):
  for b in get_root_bins():
    add_element(b, config.root_bin, indent + indent_char)
    #element = pads[pad].split(':')[0]
    #print '"',pads[pad].split(':')[0],'"' , '->', '"',pad,'";'


#connection
def create_connection(indent):
  for pad in g_pads:
    add_connection(pad.peer_name, pad.name, indent)

def format_gst_line(line):
    ansi_escape = re.compile(r'\x1b[^m]*m')
    line = ansi_escape.sub('\t', line)
    tab = re.split(r'\t+', line)
    line = tab.pop()
    return line

def parse_file(filename):
  for line in fileinput.input([filename]):
      mobj = re.match(r".*linked.*successful", line)
      #get pads
      if mobj:
          line = format_gst_line(mobj.group())
          tab = re.split(r'\t+', line)
          line = tab.pop()
          tab = line.split('and')
          name = tab[1].replace(', successful','').strip()
          peer_name = tab[0].replace('linked','').strip()
          g_pads.append(Pad(name, peer_name))
          g_pads.append(Pad(peer_name, name))
      #get elements and bins
      mobj = re.match(r".*adding element.*", line)
      if mobj:
        line = format_gst_line(mobj.group())
        tab = line.split(' to ')
        #print line
        gst_bin = tab[1].replace('bin ','').strip()
        gst_element = tab[0].replace('adding element ','').strip()
        if gst_element == 'uridecodebin0':
          config.root_bin = Element(gst_bin, None)

        if new_bin (gst_bin):
          g_bins.append(gst_bin)
        el = get_element_by_name(gst_element)
        if el is None:
          g_elements.append(Element(gst_element, gst_bin))
        else:
          el.bin_name = gst_bin

      #get elements name and type
      #mobj = re.match(r".*creating element.*", line)
      #if mobj:
      #  line = format_gst_line(mobj.group())

      #detect playbin
      mobj = re.match(r".*created element.*", line)
      if mobj:
          line = format_gst_line(mobj.group())
          if 'playbin' in line:
              config.has_playbin = True
      #detect playbin URI
      mobj = re.match(r".*set new uri to.*", line)
      if mobj:
          line = format_gst_line(mobj.group())
          tab = line.split(' to ')
          config.extra_root_bin_comments += '\\ncurrent-uri=\\"%s\\"' % tab[1]

def show_elements():
  elements ='\\lelements:'
  for e in g_elements:
    elements += '\\l%s in bin %s' % (e.name, e.bin_name)
  return elements

def show_pads():
  pads ='\\lpads:'
  for p in g_pads:
      pads += '\\l%s -> %s' % (p.name,p.peer_name)
  return pads


#Start of the program.
input_filename = '-'
try:
  input_filename = sys.argv[1]
except:
  print "Use stdin as input method"
  input_filename = '-'

stdout = sys.stdout
try:
  f = open(sys.argv[2],'w')
  sys.stdout = f
except:
  sys.stdout = stdout

parse_file(input_filename)

print 'digraph pipeline {'
print indent_char,'rankdir=LR;'
print indent_char,'fontname="sans";'
print indent_char,'fontsize="10";'
print indent_char,'labelloc=t;'
print indent_char,'nodesep=.1;'
print indent_char,'ranksep=.2;'
print indent_char,'label="<GstPipeline>\\n%s\\n[>]%s";' % (config.root_bin.name, config.extra_root_bin_comments)
print indent_char,'node [style="filled,rounded", shape=box, fontsize="9", fontname="sans", margin="0.0,0.0"];'
print indent_char,'edge [labelfontsize="6", fontsize="9", fontname="monospace"];'
print indent_char,'legend ['
print indent_char,'pos="0,0!",'
print indent_char,'margin="0.05,0.05",'
print indent_char,'style="filled"'
print indent_char, 'label="Legend\l%s\l%s"' %  (show_elements(), show_pads())
print indent_char,'];'
print '\n'

# create the graph
create_subgraph('')
#create_connection('')
print '}'
