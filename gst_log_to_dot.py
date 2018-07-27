# usage :
# $ cat file.log | python gobj-log-2-graph.py > mygraph.dot
# $ dot -Tsvg mygraph.dot mygraph.svg
#
# if something:
# dot is in graphviz package
# apt install graphviz

import re
import fileinput

# 'obj' : 'parent'

g_pads = {}
g_elements = {}
g_bins = []
g_graph_elements = []
indent_char = '\t'

class Config:
    has_playbin = False
    root_bin = 'pipeline0'
config = Config() 

def new_element_in_graph (element):
  for el in g_graph_elements:
    if el == element:
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
    if g_elements[e] == '(NULL)':
      root_bins.append(e)
  return root_bins

def get_elements_from_bin(bin_el):
  elements = []
  for e in g_elements:
    if g_elements[e] == bin_el:
      elements.append(e)
  return elements

def get_pad_for_element(element):
  pads = []
  for p in g_pads:
    pad = p.split(':')[0]
    if p.split(':')[0] == element:
      pads.append(p)
    if g_pads[p].split(':')[0] == element:
      pads.append(g_pads[p])
  return pads
      
def beautify_name(name):
  for r in [':', '-']:
    name = name.replace(r, '_')
  return name

def add_connection(pad_sink, pad_src, indent, label=''):
  print indent,'%s -> %s %s' %(beautify_name(pad_sink),beautify_name(pad_src), label)

def add_pad(pad_name, indent):
  body_indent = indent + indent;
  print indent,'subgraph ',beautify_name(pad_name),'{'
  print body_indent,'label="";'
  print body_indent,'style="invis";'
  if 'sink' in pad_name:
    print body_indent,beautify_name(pad_name),'[color=black, fillcolor="#aaaaff", label="sink\\n[>][bfb]", height="0.2", style="filled,solid"];'
  else:
    print body_indent,beautify_name(pad_name),'[color=black, fillcolor="#aaaaff", label="src\\n[>][bfb]", height="0.2", style="filled,solid"];'
  print indent,'}'

def add_element (element, parent_bin, indent):
  if new_element_in_graph(element):
    body_indent = indent + indent;
    print indent,'subgraph cluster_%s {' % beautify_name(element)
    print body_indent,'fontname="Bitstream Vera Sans";'
    print body_indent,'fontsize="8";'
    print body_indent,'style="filled,rounded";'
    print body_indent,'color=black;'
    print body_indent,'label="%s\\n[>]\\nparent=(GstPipeline) %s"' % (beautify_name(element), parent_bin)
    for p in get_pad_for_element(element):
      add_pad(p, indent + indent_char)

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
    add_connection(g_pads[pad], pad, indent)

def format_gst_line(line):
    ansi_escape = re.compile(r'\x1b[^m]*m')
    line = ansi_escape.sub('\t', line)
    tab = re.split(r'\t+', line)
    line = tab.pop()
    return line

def parse_file():
  for line in fileinput.input():
      mobj = re.match(r".*linked.*successful", line)
      #get pads
      if mobj:
          line = format_gst_line(mobj.group())
          tab = re.split(r'\t+', line)
          line = tab.pop()
          tab = line.split('and')
          
          g_pads[tab[1].replace(', successful','').strip()] = tab[0].replace('linked','').strip()
      #get elements and bins
      mobj = re.match(r".*adding element.*", line)
      if mobj:
        line = format_gst_line(mobj.group())
        tab = line.split(' to ')
        #print line
        gst_bin = tab[1].replace('bin ','').strip()
        gst_element = tab[0].replace('adding element ','').strip()
        if gst_element == 'uridecodebin0':
          config.root_bin = gst_bin
          print '///coucououcouc%s' % config.root_bin
        if new_bin (gst_bin):
          g_bins.append(gst_bin)
        g_elements[gst_element] = gst_bin
      #detect playbin
      mobj = re.match(r".*created element.*", line)
      if mobj:
          line = format_gst_line(mobj.group())
          if 'playbin' in line:
              config.has_playbin = True
          print '///%s' % line
          

def show_elements():
  for e in g_elements:
    print '//%s in bin %s' % (e,g_elements[e])

def show_pads():
  for p in g_pads:
      print '//%s -> %s' % (p,g_pads[p])

parse_file()
if g_pads:
  show_elements()
  show_pads()
  print 'digraph pipeline {'
  print indent_char,'rankdir=LR;'
  print indent_char,'fontname="sans";'
  print indent_char,'fontsize="10";'
  print indent_char,'labelloc=t;'
  print indent_char,'nodesep=.1;'
  print indent_char,'ranksep=.2;'
  print indent_char,'label="<GstPipeline>\\n%s\\n[>]";' % config.root_bin
  print indent_char,'node [style="filled,rounded", shape=box, fontsize="9", fontname="sans", margin="0.0,0.0"];'
  print indent_char,'edge [labelfontsize="6", fontsize="9", fontname="monospace"];'
  print '\n'
  create_subgraph('')
  create_connection('')
  print '}'
