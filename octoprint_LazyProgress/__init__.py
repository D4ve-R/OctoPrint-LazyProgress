#OctoPrint-LazyProgress
#Copyright (C) 2022  David Rechkemmer
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

# coding=utf-8
from __future__ import absolute_import
import math
from octoprint.printer import PrinterCallback
from octoprint.events import Events
import octoprint.plugin

class ProgressMonitor(PrinterCallback):
    def __init__(self, *args, **kwargs):
        super(ProgressMonitor, self).__init__(*args, **kwargs)
        self.reset()

    def reset(self):
        self.completion = None
        self.time_elapsed_s = None
        self.time_left_s = None

    def on_printer_send_current_data(self, data):
        self.completion = data["progress"]["completion"]
        self.time_elapsed_s = data["progress"]["printTime"]
        self.time_left_s = data["progress"]["printTimeLeft"]


class LazyProgressPlugin(
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.ProgressPlugin,
    octoprint.plugin.EventHandlerPlugin,
):

    def on_after_startup(self):
        self._progress = ProgressMonitor()
        self._printer.register_callback(self._progress)
    
    
    def on_event(self, event, payload):
        if event == Events.PRINT_STARTED or event == Events.PRINT_DONE:
            if payload.get("origin", "") == "sdcard":
                return

        if event == Events.PRINT_STARTED:
            self._progress.reset()
            self._set_progress(0)
        elif event == Events.PRINT_DONE:
            self._set_progress(100, 0)


    def on_print_progress(self, storage, path, progress):
        if not self._printer.is_printing():
            return

        if storage == "sdcard":
            return

        progress = 0.0
        time_left = None

        if self._progress.time_left_s is not None:
            time_left = self._progress.time_left_s
        if (self._progress.time_left_s is not None and self._progress.time_elapsed_s is not None):
            time_left_s = self._progress.time_left_s
            time_elapsed_s = self._progress.time_elapsed_s
            progress = time_elapsed_s / (time_left_s + time_elapsed_s)
            progress = progress * 100.0
        else:
            progress = self._progress.completion or 0.0
        self._set_progress(progress=progress, time_left=time_left)

    def _set_progress(self, progress, time_left=None):
        if time_left is None:
            gcode = f"M117 P {progress:.2f}%"
        else:
            mins = math.floor(time_left / 60)
            hrs = math.floor(mins / 60)
            mins = mins - (hrs * 60)
            gcode = f"M117 P{progress:.2f}% T{hrs}::{mins}"

        self._printer.commands(gcode)

    ##~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "LazyProgress": {
                "displayName": "LazyProgress Plugin",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "D4ve-R",
                "repo": "OctoPrint-LazyProgress",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/D4ve-R/OctoPrint-LazyProgress/archive/{target_version}.zip",
            }
        }

# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "LazyProgress"

# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
#__plugin_pythoncompat__ = ">=2.7,<3" # only python 2
__plugin_pythoncompat__ = ">=3,<4" # only python 3
#__plugin_pythoncompat__ = ">=2.7,<4" # python 2 and 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = LazyProgressPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
        }
