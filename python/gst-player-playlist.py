import gi
import argparse
import os
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gst, GLib

WORKING_DIR = os.path.dirname(os.path.abspath(__file__))

class PlayEngine:
    def __init__(self, options):
        Gst.init(None)
        self.options = options

        if not options.uri_pattern and not options.uri:
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

        if self.options.uri_pattern:
            next_uri = self.options.uri_pattern.format(self.uri_played)
            self.playbin.set_property('uri', "file://" + next_uri)
        else:
            self.playbin.set_property('uri', "file://" + self.options.uri)

        self.playbin.set_state(Gst.State.PLAYING)

        self.loop = GLib.MainLoop()
        self.loop.run()

    def on_eos(self, bus, msg):
        print('Quitting on eos')
        self.playbin.set_state(Gst.State.NULL)
        self.loop.quit()

    def on_about_to_finish(self, playbin):
        print('In on_about_to_finish')
        self.uri_played += 1
        if self.options.uri_pattern:
          next_uri = self.options.uri_pattern.format(self.uri_played)
          self.playbin.set_property('uri', "file://" + next_uri)
        if self.options.next_uri:
            self.playbin.set_property('uri', "file://" + self.options.next_uri)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="gst-player-playbin-about")
    parser.add_argument('-i', dest="uri", help="input uri")
    parser.add_argument('-n','--next-uri', nargs='?', default='', dest="next_uri", help="The next uri")
    parser.add_argument('-p','--uri-pattern', nargs='?', default='', dest="uri_pattern", help="The uri pattern such as path-{}.ext")
    parser.add_argument('--playbin', dest='playbin', action='store_true', help="Use old playbin")
    options = parser.parse_args()
    play_engine = PlayEngine(options)
