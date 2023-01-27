# window.py
#
# Copyright 2023 Lorenzo Paderi
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import pulsectl
import time
from gi.repository import Adw
from gi.repository import Gtk
from pprint import pprint
from ..utils import async_utils
from ..pipewire.pipewire import Pipewire, PwLink


class PwActiveConnectionBox(Adw.PreferencesGroup):
    def __init__(self, input_link: PwLink, output_link: PwLink, connection_name: str, link_ids: list[str], disconnect_cb: callable, **kwargs):
        super().__init__(css_classes=['boxed-list'])

        self.input_link = input_link
        self.output_link = output_link
        self.input_name = input_link.name
        self.output_name = output_link.name
        self.link_ids = link_ids
        
        self.disconnect_cb = disconnect_cb
        self.set_title(connection_name)
        self.set_description('Link IDs: '+ ', '.join(link_ids))

        self.output_exp = Adw.ExpanderRow(title=self.output_name)
        self.input_exp = Adw.ExpanderRow(title=self.input_name)

        self.output_exp.add_prefix(Gtk.Image.new_from_icon_name('microphone2-symbolic'))
        self.input_exp.add_prefix(Gtk.Image.new_from_icon_name('audio-speaker-symbolic'))

        self.input_range = Gtk.Scale()
        self.input_range.connect('change-value', self.on_change_input_range)
        self.input_range.set_range(0, 100)
        self.output_range = Gtk.Scale()
        self.output_range.connect('change-value', self.on_change_output_range)
        self.output_range.set_range(0, 100)

        inp_r = Gtk.ListBoxRow()
        inp_r.set_child(self.input_range)
        outp_r = Gtk.ListBoxRow()
        outp_r.set_child(self.output_range)

        self.input_exp.add_row(inp_r)
        self.output_exp.add_row(outp_r)

        self.add(self.output_exp)
        self.add(self.input_exp)

        disconnect_btn = Gtk.Button(label='Disconnect', css_classes=['destructive-action'])
        disconnect_btn.connect('clicked', self.on_disconnect_btn_clicked)

        self.header_suffix = disconnect_btn
        self.set_header_suffix(self.header_suffix)
        
        self.pa_sink = None
        self.pa_source = None
        self.refresh_volume_levels()
        
    def refresh_volume_levels(self):
        self.pa_sink = pulsectl.Pulse(client_name='it.mijorus.whisper').get_sink_by_name(self.input_link.resource_name)
        self.pa_source = pulsectl.Pulse(client_name='it.mijorus.whisper').get_source_by_name(self.output_link.resource_name)
        
        self.input_range.set_value(self.pa_sink.volume.value_flat * 100)
        self.output_range.set_value(self.pa_source.volume.value_flat * 100)
    
    def on_disconnect_btn_clicked(self, _):
        self.disconnect_cb(self.link_ids)
    
    @async_utils.debounce(0.5)
    def on_change_input_range(self, widget, _, value: float):
        if self.pa_sink:
            pulsectl.Pulse().volume_set_all_chans(self.pa_sink, (value / 100))
    
    @async_utils.debounce(0.5)
    def on_change_output_range(self, widget, _, value: float):
        if self.pa_source:
            pulsectl.Pulse().volume_set_all_chans(self.pa_source, (value / 100))