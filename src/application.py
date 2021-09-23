# application.py
#
# This file is part of Wike, a Wikipedia Reader for the GNOME Desktop.
# Copyright 2021 Hugo Olabera <hugolabe@gmail.com>.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import sys

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Handy', '1')
from gi.repository import Gio, GLib, Gtk, Handy

from wike.data import settings, languages, historic, bookmarks
from wike.prefs import PrefsWindow
from wike.view import view_settings
from wike.window import Window


# Main application class
# Wike Wikipedia Reader

class Application(Gtk.Application):

  # Initialize app

  def __init__(self):
    super().__init__(application_id='com.github.hugolabe.Wike', flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

    self._window = None
    self._launch_uri = ''

    self.add_main_option('url', b'u', GLib.OptionFlags.NONE, GLib.OptionArg.STRING, 'Wikipedia URL to open', None)

  # Initialize libhandy and set actions

  def do_startup(self):
    Gtk.Application.do_startup(self)

    Handy.init()

    action = Gio.SimpleAction.new('prefs', None)
    action.connect('activate', self._prefs_cb)
    self.add_action(action)
    self.set_accels_for_action('app.prefs', ('<Ctrl>E',))

    action = Gio.SimpleAction.new_stateful('dark_mode', None, GLib.Variant.new_boolean(settings.get_boolean('dark-mode')))
    action.connect('change-state', self._dark_mode)
    self.add_action(action)

    action = Gio.SimpleAction.new('shortcuts', None)
    action.connect('activate', self._shortcuts_cb)
    self.add_action(action)
    self.set_accels_for_action('app.shortcuts', ('<Ctrl>question',))

    action = Gio.SimpleAction.new('about', None)
    action.connect('activate', self._about_cb)
    self.add_action(action)

    action = Gio.SimpleAction.new('quit', None)
    action.connect('activate', self._quit_cb)
    self.add_action(action)
    self.set_accels_for_action('app.quit', ('<Ctrl>Q',))

  # Manage command line options

  def do_command_line(self, command_line):
    options = command_line.get_options_dict().end().unpack()

    if 'url' in options:
      self._launch_uri = options['url']

    if self._window:
      self._window.new_page(self._launch_uri, None, True)

    self.activate()
    return 0

  # Create main window and connect delete event

  def do_activate(self):
    if not self._window:
      self._window = Window(self, self._launch_uri)
      self._window.connect('delete-event',self._window_delete_cb)
      self._gtk_settings = Gtk.Settings.get_default()
      if settings.get_boolean('dark-mode'):
        self._gtk_settings.set_property('gtk-application-prefer-dark-theme', True)
      self._window.show_all()
    else:
      self._window.present()

  # Show Preferences window

  def _prefs_cb(self, action, parameter):
    prefs_window = PrefsWindow()
    prefs_window.set_transient_for(self._window)
    prefs_window.show_all()

  # Set/unset dark mode for UI and view

  def _dark_mode(self, action, parameter):
    action.set_state(parameter)
    settings.set_boolean('dark-mode', parameter)
    self._gtk_settings.set_property('gtk-application-prefer-dark-theme', parameter)
    view_settings.set_style()

  # Show Shortcuts window

  def _shortcuts_cb(self, action, parameter):
    builder = Gtk.Builder()
    builder.add_from_resource("/com/github/hugolabe/Wike/ui/shortcuts.ui")
    shortcuts_window = builder.get_object("shortcuts_window")
    shortcuts_window.set_transient_for(self._window)
    shortcuts_window.show()

  # Show About dialog

  def _about_cb(self, action, parameter):
    builder = Gtk.Builder()
    builder.add_from_resource("/com/github/hugolabe/Wike/ui/about.ui")
    about_dialog = builder.get_object("about_dialog")
    about_dialog.set_transient_for(self._window)
    about_dialog.run()
    about_dialog.destroy()

  # On window delete quit app

  def _window_delete_cb(self, window, event):
    quit_action = self.lookup_action('quit')
    quit_action.activate()

  # Save settings and data and quit app

  def _quit_cb(self, action, parameter):
    if self._window.is_maximized():
      settings.set_boolean('window-max', True)
    else:
      settings.set_boolean('window-max', False)
      size = self._window.get_size()
      settings.set_int('window-width', size[0])
      settings.set_int('window-height', size[1])

    if self._window.page.wikiview.is_local():
      settings.set_string('last-uri', '')
    else:
      settings.set_string('last-uri', self._window.page.wikiview.get_base_uri())

    settings.sync()
    languages.save()
    if not settings.get_boolean('keep-historic'):
      historic.clear()
    historic.save()
    bookmarks.save()

    self.quit()


# Run app

def main(version):
  app = Application()
  return app.run(sys.argv)

