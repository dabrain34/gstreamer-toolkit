import gi
import argparse
import os
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gst, GLib

WORKING_DIR = os.path.dirname(os.path.abspath(__file__))

class PlayEngine:

    def read_playlist_file(self):
      self.playlist = []
      with open(self.options.playlist_file) as f:
          self.playlist = [line.rstrip() for line in f]
      if self.playlist:
        if not os.path.isabs(self.playlist[0]):
          playlist = []
          for f in self.playlist:
            playlist += [os.path.join(os.path.dirname(self.options.playlist_file),f)]
          self.playlist = playlist

      if options.reverse:
        self.playlist.reverse()
      for f in self.playlist:
        print(f)

    def read_playlist_pattern(self):
      self.playlist = []
      i = 0
      while True:
        next_uri = self.options.uri_pattern.format(i)
        print(" File path is invalid:" + next_uri)
        if(not os.path.isfile(next_uri)):
          break
        else:
          self.playlist += [next_uri]
          i += 1
      if options.reverse:
         self.playlist.reverse()

    def __init__(self, options):
        Gst.init(None)
        self.options = options
        self.playlist = []
        if not options.playlist_file and not options.uri_pattern and not options.uri:
          print("Usage: %s --help" % __file__)
          exit(1)

        if self.options.playbin:
            print("use old playbin")
            self.playbin = Gst.ElementFactory.make('playbin', None)
        else:
            self.playbin = Gst.ElementFactory.make('playbin3', None)
        self.playbin.connect('about-to-finish', self.on_about_to_finish)
        self.uri_played = 0

        self.bus = self.playbin.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message::eos', self.on_eos)

        if self.options.playlist_file:
            self.read_playlist_file()
        elif self.options.uri_pattern:
            self.read_playlist_pattern()
        else:
            self.playlist += [self.options.uri]

        if self.playlist and os.path.isfile(self.playlist[0]):
          self.playbin.set_property('uri', "file://" + self.playlist[0])
        else:
          if self.playlist:
            print(" File is invalid:" + self.playlist[0])
          print("Usage: %s --help" % __file__)
          exit(1)

        self.playbin.set_state(Gst.State.PLAYING)

        self.loop = GLib.MainLoop()
        self.loop.run()

    def on_eos(self, bus, msg):
        print('Quitting on eos')
        self.playbin.set_state(Gst.State.NULL)
        self.loop.quit()

    def on_about_to_finish(self, playbin):
        print('on_about_to_finish')
        next_uri = ''
        self.uri_played += 1
        if self.uri_played < len(self.playlist)  and os.path.isfile(self.playlist[self.uri_played]):
          next_uri = self.playlist[self.uri_played]
        elif self.options.next_uri:
          next_uri = self.options.next_uri

        if next_uri:
          print('next uri is' + next_uri)
          self.playbin.set_property('uri', "file://" + next_uri)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="gst-player-playbin-about")
    parser.add_argument('-u', '--uri', dest="uri", help="input uri")
    parser.add_argument('-r', '--reverse', dest='reverse', action='store_true', help="Reverse the playlist")
    parser.add_argument('-n','--next-uri', nargs='?', default='', dest="next_uri", help="The next uri")
    parser.add_argument('--uri-pattern', nargs='?', default='', dest="uri_pattern", help="The uri pattern such as path-{}.ext")
    parser.add_argument('-p','--playlist-file', nargs='?', default='', dest="playlist_file", help="The playlist file path")
    parser.add_argument('--playbin', dest='playbin', action='store_true', help="Use old playbin")
    options = parser.parse_args()
    play_engine = PlayEngine(options)
