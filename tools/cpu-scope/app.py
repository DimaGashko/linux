#!/usr/bin/env python3
"""CPU Scope: native GTK4 UI; history queries run off the GTK thread."""
import argparse
import colorsys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import math
import os
import signal
from pathlib import Path
import time

# Simple static plots do not need a GPU renderer or its driver allocations.
os.environ.setdefault('GSK_RENDERER', 'cairo')
if os.environ['GSK_RENDERER'] == 'cairo':
    os.environ.setdefault('GDK_DISABLE', 'gl,vulkan')
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gdk, GLib, GObject, Gtk

from storage import data_dir, query, runtime_dir
from stress_test import StressTest

RANGES = [('1 minute', 60), ('5 minutes', 300), ('15 minutes', 900), ('1 hour', 3600),
          ('6 hours', 21600), ('24 hours', 86400), ('7 days', 604800), ('30 days', 2592000), ('All history', 0)]
CSS = b'''
window { background: #101215; color: #e2e5e7; }
headerbar { background: #15181c; border-bottom: 1px solid #242a31; }
.sidebar { background: #15181c; border-right: 1px solid #242a31; }
.sidebar row { border-radius: 4px; margin: 1px 8px; padding: 5px 8px; }
.sidebar row:selected { background: #243339; }
.sidebar row:hover { background: #20272d; }
.sidebar list { background: transparent; }
.caption { color: #929da7; font-size: 11px; }
.mono { font-family: monospace; }
.number { font-size: 27px; font-weight: 500; font-family: monospace; }
.section { font-size: 11px; font-weight: 700; letter-spacing: 1px; color: #a3adb5; }
.frequency { color: #7fc6b5; }
.usage { color: #dfb574; }
.status { color: #a4b8b0; font-size: 12px; }
button { border-radius: 5px; background: #20252b; }
button:hover { background: #2b333b; }
button:checked { background: #29413f; color: #a2e0cf; }
entry { background: #191e23; }
.legend button { padding: 2px 6px; min-height: 22px; background: transparent; }
progressbar trough { min-height: 3px; background: #282f36; }
progressbar progress { min-height: 3px; background: #dfb574; }
progressbar text { font-size: 10px; color: #b8a383; }
entry { border-radius: 5px; }
'''


def cpu_color(cpu):
    return colorsys.hsv_to_rgb((cpu * .61803398875 + .43) % 1, .48 + (cpu % 2) * .18, .88)


def cpu_name(cpu):
    """One-based display name for a zero-based Linux logical CPU index."""
    return f'CPU {cpu + 1:02}'


def label(text='', css=None, xalign=0):
    w = Gtk.Label(label=text, xalign=xalign)
    if css:
        for name in css.split():
            w.add_css_class(name)
    return w


def box(vertical=False, spacing=8):
    return Gtk.Box(orientation=Gtk.Orientation.VERTICAL if vertical else Gtk.Orientation.HORIZONTAL, spacing=spacing)


def margin(widget, amount):
    for side in ('top', 'bottom', 'start', 'end'):
        getattr(widget, 'set_margin_' + side)(amount)
    return widget


class ModeSwitch(Gtk.Box):
    __gsignals__ = {'changed': (GObject.SignalFlags.RUN_FIRST, None, ())}

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.add_css_class('linked')
        self.buttons = [Gtk.ToggleButton(label=title) for title in ('Average', 'Separate CPUs')]
        self.buttons[1].set_group(self.buttons[0])
        self.buttons[0].set_active(True)
        for button in self.buttons:
            button.connect('toggled', self.toggled)
            self.append(button)

    def toggled(self, button):
        if button.get_active():
            self.emit('changed')

    def get_selected(self):
        return int(self.buttons[1].get_active())

    def set_selected(self, index):
        self.buttons[index].set_active(True)


class Chart(Gtk.DrawingArea):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.pointer = None
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_content_height(330)
        self.set_draw_func(self.draw)
        motion = Gtk.EventControllerMotion()
        motion.connect('motion', self.motion)
        motion.connect('leave', self.leave)
        self.add_controller(motion)
        scroll = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.BOTH_AXES)
        scroll.connect('scroll', self.scroll)
        self.add_controller(scroll)
        drag = Gtk.GestureDrag()
        drag.connect('drag-begin', self.drag_begin)
        drag.connect('drag-update', self.drag_update)
        self.add_controller(drag)

    def motion(self, _, x, y):
        self.pointer = (x, y)
        self.queue_draw()

    def leave(self, *_):
        self.pointer = None
        self.queue_draw()

    def scroll(self, controller, dx, dy):
        if controller.get_current_event_state() & Gdk.ModifierType.CONTROL_MASK:
            self.owner.zoom(1 if dy > 0 else -1)
        else:
            self.owner.pan((dx or dy) * .12)
        return True

    def drag_begin(self, *_):
        self.drag_end_time = self.owner.end

    def drag_update(self, _, dx, dy):
        self.owner.set_end(self.drag_end_time - dx / max(1, self.get_width() - 85) * self.owner.span())

    def draw(self, area, cr, width, height):
        o = self.owner
        left, right = 64, width - 18
        plot_width = max(1, right - left)
        start, end = o.end - o.span(), o.end
        cr.select_font_face('Sans')

        def text(x, y, value, size=11, color=(.56, .61, .65)):
            cr.set_source_rgb(*color)
            cr.set_font_size(size)
            cr.move_to(x, y)
            cr.show_text(str(value))

        freq_top, freq_bottom = 32, height * .55
        load_top, load_bottom = height * .64, height - 42
        text(left, 16, 'FREQUENCY · MHz', color=(.50, .78, .71))
        text(left, load_top - 13, 'UTILIZATION · %', color=(.87, .71, .45))
        max_freq = max(1000, o.max_frequency, max((p[1][3] for points in o.series.values() for p in points), default=0))
        ceiling = math.ceil(max_freq / 1000) * 1000
        for top, bottom, limit in ((freq_top, freq_bottom, ceiling), (load_top, load_bottom, 100)):
            for i in range(5):
                y = bottom - (bottom - top) * i / 4
                cr.set_source_rgb(.14, .17, .20)
                cr.set_line_width(.6)
                cr.move_to(left, y)
                cr.line_to(right, y)
                cr.stroke()
                text(8, y + 4, f'{limit * i / 4:,.0f}')
        for i in range(6):
            x = left + plot_width * i / 5
            stamp = start + (end - start) * i / 5
            dt = datetime.fromtimestamp(stamp)
            fmt = '%H:%M:%S' if o.span() <= 300 else '%H:%M' if o.span() < 86400 else '%d %b'
            text(max(left, min(x - 23, right - 53)), height - 15, dt.strftime(fmt))
            cr.set_source_rgba(.35, .39, .43, .2)
            cr.move_to(x, freq_top)
            cr.line_to(x, load_bottom)
            cr.stroke()

        # Clip every mark; only bounded visible points exist in memory.
        cr.save()
        cr.rectangle(left, freq_top, plot_width, load_bottom - freq_top + 1)
        cr.clip()
        for top, bottom, limit, col, mean_i, min_i, max_i in (
            (freq_top, freq_bottom, ceiling, (.50, .78, .71), 1, 2, 3),
            (load_top, load_bottom, 100, (.87, .71, .45), 4, 5, 6),
        ):
            for cpu, points in o.series.items():
                if o.separate():
                    col = cpu_color(cpu)
                segments, segment, last = [], [], None
                for t, values in points:
                    if last is not None and t - last > o.step * 2:
                        if segment:
                            segments.append(segment)
                        segment = []
                    last = t
                    x = left + (t - start) / max(1, end - start) * plot_width
                    y = lambda value: bottom - value / limit * (bottom - top)
                    segment.append((x, y(values[mean_i] / values[0]), y(values[min_i]), y(values[max_i])))
                if segment:
                    segments.append(segment)
                for s in segments:
                    cr.set_source_rgba(*col, 0 if o.separate() else .14)
                    cr.move_to(s[0][0], s[0][2])
                    for x, mean, lo, hi in s:
                        cr.line_to(x, lo)
                    for x, mean, lo, hi in reversed(s):
                        cr.line_to(x, hi)
                    cr.close_path()
                    cr.fill()
                    cr.set_source_rgb(*col)
                    cr.set_line_width(1.1 if o.separate() else 1.6)
                    cr.move_to(s[0][0], s[0][1])
                    for x, mean, lo, hi in s:
                        cr.line_to(x, mean)
                    cr.stroke()
                    if len(s) == 1:
                        cr.arc(s[0][0], s[0][1], 2, 0, math.tau)
                        cr.fill()
        cr.restore()
        if not any(o.series.values()):
            text(left + 20, freq_top + 50, 'No recorded samples in this window', 14)
        if self.pointer and left <= self.pointer[0] <= right and any(o.series.values()):
            x = self.pointer[0]
            stamp = start + (x - left) / plot_width * (end - start)
            nearest = [(cpu, min(points, key=lambda p: abs(p[0] - stamp)))
                       for cpu, points in o.series.items() if points]
            is_load = self.pointer[1] >= load_top
            top, bottom, limit, idx = (load_top, load_bottom, 100, 4) if is_load else (freq_top, freq_bottom, ceiling, 1)
            cpu, (t, v) = min(nearest, key=lambda item: abs(
                bottom - item[1][1][idx] / item[1][1][0] / limit * (bottom - top) - self.pointer[1]))
            cr.set_source_rgba(.8, .85, .88, .5)
            cr.move_to(x, freq_top)
            cr.line_to(x, load_bottom)
            cr.stroke()
            tip = f'{datetime.fromtimestamp(t):%d %b %H:%M:%S}   {v[1]/v[0]:,.0f} MHz   {v[4]/v[0]:.1f}%'
            if o.separate():
                tip = f'{cpu_name(cpu)} · ' + tip
            tx = min(max(left, x - 190), max(left, right - 430))
            cr.set_source_rgb(.12, .15, .18)
            cr.rectangle(tx - 6, freq_top + 9, 436, 28)
            cr.fill()
            text(tx, freq_top + 28, tip, 12, (.88, .91, .93))


class Window(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title='CPU Scope')
        self.set_default_size(1080, 760)
        self.set_size_request(820, 600)
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='history')
        self.future = None
        self.closed = False
        self.stress = StressTest()
        self.stress_deadline = 0
        self.dirty = True
        self.generation = 0
        self.points = []
        self.series = {}
        self.legend_cpus = ()
        self.step = 1
        self.extent = None
        self.cpu = -1
        self.end = time.time()
        self.live = True
        self.range_index = 1
        self.rows = {}
        self.latest = {}
        self.last_query = 0
        self.average_seconds = 1
        self.refresh_seconds = 1
        self.max_frequency = 4000
        try:
            self.max_frequency = max(int(p.read_text()) / 1000 for p in Path('/sys/devices/system/cpu').glob('cpu[0-9]*/cpufreq/cpuinfo_max_freq'))
        except (OSError, ValueError):
            pass
        self.build()
        self.connect('close-request', self.on_close)
        self.timer = GLib.timeout_add(250, self.tick)
        self.readings_timer = GLib.timeout_add(1000, self.refresh_readings)
        self.refresh_readings()
        self.tick()

    def build(self):
        root = box(True, 0)
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title='CPU Scope', subtitle='Processor frequency & utilization'))
        self.live_button = Gtk.Button(label='● Live')
        self.live_button.set_tooltip_text('Return to the newest samples')
        self.live_button.connect('clicked', self.go_live)
        header.pack_end(self.live_button)
        root.append(header)
        body = box(False, 0)
        body.set_vexpand(True)
        root.append(body)
        sidebar = box(True, 10)
        sidebar.add_css_class('sidebar')
        sidebar.set_size_request(240, -1)
        sidebar.append(margin(label('LOGICAL CPUs  ·  LIVE', 'section'), 16))
        self.core_list = Gtk.ListBox()
        self.core_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.core_list.connect('row-selected', self.select_core)
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_vexpand(True)
        scroller.set_child(self.core_list)
        sidebar.append(scroller)
        sidebar.append(margin(label('Select a CPU to inspect its history.\nMHz = clock speed, % = busy time.', 'caption'), 12))
        body.append(sidebar)
        main = margin(box(True, 16), 22)
        main.set_hexpand(True)
        body.append(main)
        self.title_label = label('All CPUs', None)
        self.title_label.add_css_class('title-2')
        heading = box(False, 12)
        self.title_label.set_hexpand(True)
        heading.append(self.title_label)
        self.mode_widget = ModeSwitch()
        self.mode_widget.set_tooltip_text('Show one average or a separate colored line for every logical CPU')
        self.mode_widget.connect('changed', self.change_mode)
        heading.append(self.mode_widget)
        main.append(heading)
        stats = box(False, 30)
        self.mhz_label, self.usage_label, self.temp_label = label('—', 'number frequency'), label('—', 'number usage'), label('—', 'number')
        for title, value in (('CURRENT MHz', self.mhz_label), ('CURRENT UTILIZATION', self.usage_label), ('CPU TEMPERATURE', self.temp_label)):
            group = box(True, 5)
            group.append(label(title, 'section'))
            group.append(value)
            stats.append(group)
        main.append(stats)
        toolbar = box(False, 6)
        self.range_widget = Gtk.DropDown.new_from_strings([x[0] for x in RANGES])
        self.range_widget.set_selected(self.range_index)
        self.range_widget.connect('notify::selected', self.change_range)
        toolbar.append(self.range_widget)
        for title, amount, tip in (('←', -.8, 'Earlier window'), ('→', .8, 'Later window')):
            button = Gtk.Button(label=title)
            button.set_tooltip_text(tip)
            button.connect('clicked', lambda _, a=amount: self.pan(a))
            toolbar.append(button)
        self.date_entry = Gtk.Entry(placeholder_text='YYYY-MM-DD HH:MM')
        self.date_entry.set_width_chars(18)
        self.date_entry.set_hexpand(True)
        self.date_entry.set_tooltip_text('Local date/time for the right edge of the window. Press Enter.')
        self.date_entry.connect('activate', self.jump)
        toolbar.append(self.date_entry)
        main.append(toolbar)
        averaging = box(False, 12)
        averaging.append(label('Chart average', 'caption'))
        self.average_slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, .25, 60, .25)
        self.average_slider.set_digits(2)
        self.average_slider.set_value(1)
        self.average_slider.set_round_digits(2)
        self.average_slider.set_draw_value(False)
        self.average_slider.set_hexpand(True)
        self.average_slider.set_tooltip_text('Average samples into 0.25–60 second intervals; applies to both charts, not live readings')
        self.average_slider.connect('value-changed', self.change_average)
        averaging.append(self.average_slider)
        self.average_label = label('1 s', 'caption mono')
        averaging.append(self.average_label)
        averaging.append(label('Refresh', 'caption'))
        self.refresh_input = Gtk.SpinButton.new_with_range(.25, 30, .25)
        self.refresh_input.set_digits(2)
        self.refresh_input.set_value(1)
        self.refresh_input.set_tooltip_text('Live chart refresh interval in seconds; independent of chart averaging')
        self.refresh_input.connect('value-changed', self.change_refresh)
        averaging.append(self.refresh_input)
        averaging.append(label('s', 'caption'))
        main.append(averaging)
        self.window_label = label('', 'caption mono')
        main.append(self.window_label)
        self.chart = Chart(self)
        main.append(self.chart)
        self.legend = Gtk.FlowBox()
        self.legend.set_selection_mode(Gtk.SelectionMode.NONE)
        self.legend.set_max_children_per_line(10)
        self.legend.set_min_children_per_line(4)
        self.legend.set_row_spacing(0)
        self.legend.set_column_spacing(0)
        self.legend.add_css_class('legend')
        self.legend.set_visible(False)
        main.append(self.legend)
        self.timeline = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 1, .001)
        self.timeline.set_draw_value(False)
        self.timeline.set_tooltip_text('Scrub through the entire recorded history')
        self.timeline.connect('value-changed', self.scrub)
        self.setting_timeline = False
        main.append(self.timeline)
        self.detail_label = label('Line: mean  ·  Band: min–max  ·  Scroll/drag: pan  ·  Ctrl+scroll: zoom', 'caption')
        main.append(self.detail_label)
        self.status = label('Waiting for recorder…', 'status')
        main.append(self.status)
        stress_header = box(False, 10)
        stress_toggle = Gtk.ToggleButton(label='Stress test ▸')
        stress_toggle.set_tooltip_text('Expand CPU stress-test settings')
        stress_header.append(stress_toggle)
        self.stress_status = label('Idle · CPU only', 'caption')
        self.stress_status.set_hexpand(True)
        stress_header.append(self.stress_status)
        self.stress_button = Gtk.Button(label='Start test')
        self.stress_button.connect('clicked', self.toggle_stress)
        stress_header.append(self.stress_button)
        main.append(stress_header)
        self.stress_revealer = Gtk.Revealer()
        self.stress_revealer.set_transition_type(Gtk.RevealerTransitionType.NONE)
        controls = box(False, 12)
        self.stress_settings = controls
        self.stress_workers = Gtk.SpinButton.new_with_range(1, len(os.sched_getaffinity(0)), 1)
        self.stress_workers.set_value(len(os.sched_getaffinity(0)))
        self.stress_load = Gtk.SpinButton.new_with_range(1, 100, 5)
        self.stress_load.set_value(100)
        self.stress_duration = Gtk.SpinButton.new_with_range(1, 3600, 10)
        self.stress_duration.set_value(300)
        for title, widget in (('Workers', self.stress_workers), ('Load %', self.stress_load), ('Seconds', self.stress_duration)):
            controls.append(label(title, 'caption'))
            controls.append(widget)
        self.stress_workers.set_tooltip_text('Number of CPU workers; the scheduler chooses which CPUs run them')
        self.stress_load.set_tooltip_text('Requested utilization per worker')
        self.stress_revealer.set_child(controls)
        stress_toggle.connect('toggled', lambda button: (
            self.stress_revealer.set_reveal_child(button.get_active()),
            button.set_label('Stress test ▾' if button.get_active() else 'Stress test ▸')))
        main.append(self.stress_revealer)
        self.stress_button.set_tooltip_text('Run stress-ng with the settings below; default: all available logical CPUs, 100% load, 5 minutes')
        self.set_content(root)

    def on_close(self, *_):
        self.closed = True
        self.stress.close()
        GLib.source_remove(self.timer)
        GLib.source_remove(self.readings_timer)
        self.pool.shutdown(wait=False, cancel_futures=True)
        return False

    def toggle_stress(self, *_):
        if self.stress.process is not None:
            self.stress.stop()
            self.stress_button.set_sensitive(False)
            self.stress_status.set_text('Stopping…')
            return
        try:
            seconds = self.stress_duration.get_value_as_int()
            workers = self.stress_workers.get_value_as_int()
            load = self.stress_load.get_value_as_int()
            self.stress.start(workers, load, seconds)
        except (OSError, ValueError, RuntimeError) as exc:
            self.stress_status.set_text(str(exc))
            return
        self.stress_deadline = time.monotonic() + seconds
        self.stress_summary = f'{workers} worker(s) · {load}% load'
        self.stress_status.set_text(f'{self.stress_summary} · {seconds}s left')
        self.stress_button.set_label('Stop test')
        self.stress_settings.set_sensitive(False)
        self.go_live()

    def update_stress(self):
        if self.stress.process is None:
            return
        code = self.stress.poll()
        if code is not None:
            message = 'Stopped' if self.stress.stopping else 'Completed' if code == 0 else f'Failed (exit {code})'
            self.stress_status.set_text(message)
            self.stress_button.set_label('Start test')
            self.stress_button.set_sensitive(True)
            self.stress_settings.set_sensitive(True)
        elif not self.stress.stopping:
            remaining = max(0, math.ceil(self.stress_deadline - time.monotonic()))
            self.stress_status.set_text(f'{self.stress_summary} · {remaining}s left' if remaining else 'Finishing…')

    def change_refresh(self, widget):
        self.refresh_seconds = widget.get_value()
        if self.live:
            self.invalidate()

    def change_average(self, slider):
        self.average_seconds = slider.get_value()
        self.average_label.set_text(f'{self.average_seconds:g} s')
        self.invalidate()

    def span(self):
        return RANGES[self.range_index][1] or max(60, time.time() - (self.extent[0] if self.extent else time.time() - 60))

    def invalidate(self):
        self.generation += 1
        self.dirty = True
        self.refresh_labels()
        self.request_query()

    def set_end(self, value):
        now = time.time()
        low = (self.extent[0] + min(self.span(), now - self.extent[0])) if self.extent else now - self.span()
        self.end = min(now, max(low, value))
        self.live = self.end >= now - 2
        self.invalidate()

    def pan(self, fraction):
        self.set_end(self.end + self.span() * fraction)

    def zoom(self, direction):
        self.range_widget.set_selected(max(0, min(len(RANGES) - 1, self.range_index + direction)))

    def change_range(self, widget, *_):
        self.range_index = widget.get_selected()
        if self.range_index == len(RANGES) - 1:
            self.live = True
        self.set_end(time.time() if self.live else self.end)

    def go_live(self, *_):
        self.live = True
        self.end = time.time()
        self.invalidate()

    def jump(self, entry):
        try:
            stamp = datetime.fromisoformat(entry.get_text().strip()).timestamp()
            self.set_end(stamp)
            entry.remove_css_class('error')
        except (ValueError, OverflowError):
            entry.add_css_class('error')
            self.status.set_text('Use a local date like 2026-10-21 09:30')

    def scrub(self, scale):
        if not self.setting_timeline and self.extent:
            first = min(time.time(), self.extent[0] + self.span())
            self.set_end(first + scale.get_value() * max(1, time.time() - first))

    def separate(self):
        return self.cpu == -1 and self.mode_widget.get_selected() == 1

    def change_mode(self, *_):
        self.series = {}
        self.update_mode()
        self.invalidate()

    def update_mode(self):
        self.mode_widget.set_visible(self.cpu == -1)
        self.legend.set_visible(self.separate())
        title = 'All CPUs · separate lines' if self.separate() else 'All CPUs · average'
        self.title_label.set_text(title if self.cpu == -1 else f'{cpu_name(self.cpu)} · logical processor')

    def update_legend(self):
        cpus = tuple(sorted(self.series)) if self.separate() else ()
        if cpus == self.legend_cpus:
            return
        self.legend_cpus = cpus
        while self.legend.get_first_child():
            self.legend.remove(self.legend.get_first_child())
        for cpu in cpus:
            color = '#%02x%02x%02x' % tuple(round(c * 255) for c in cpu_color(cpu))
            name = label()
            name.set_markup(f'<span foreground="{color}">● {cpu_name(cpu)}</span>')
            button = Gtk.Button(child=name)
            button.set_tooltip_text(f'Inspect {cpu_name(cpu)} on its own')
            button.connect('clicked', lambda _, c=cpu: self.core_list.select_row(self.rows[c][0]) if c in self.rows else None)
            self.legend.append(button)

    def select_core(self, _, row):
        if row:
            self.cpu = row.cpu
            self.series = {}
            self.update_mode()
            self.update_live()
            self.invalidate()

    def update_live(self):
        cpus = self.latest.get('cpus', {})
        for key in sorted(cpus, key=int):
            cpu = int(key)
            if cpu not in self.rows:
                row = Gtk.ListBoxRow()
                row.cpu = cpu
                content = box(True, 3)
                top = box(False, 8)
                name = label('All CPUs' if cpu == -1 else cpu_name(cpu))
                name.set_hexpand(True)
                value = label('', 'mono frequency')
                top.append(name)
                top.append(value)
                content.append(top)
                progress = Gtk.ProgressBar()
                content.append(progress)
                row.set_child(content)
                self.core_list.append(row)
                self.rows[cpu] = (row, value, progress)
                if cpu == self.cpu:
                    self.core_list.select_row(row)
            row, value, progress = self.rows[cpu]
            f, u = cpus[key]
            value.set_text(f'{f:,.0f} MHz')
            progress.set_fraction(u / 100)
            row.set_tooltip_text(f'{f:,.0f} MHz · {u:.1f}% utilization')
        for cpu, (row, value, progress) in self.rows.items():
            if str(cpu) not in cpus:
                value.set_text('offline')
                progress.set_fraction(0)
        values = cpus.get(str(self.cpu))
        stale = time.time() - self.latest.get('ts', 0) > 5
        self.mhz_label.set_text(f'{values[0]:,.0f}' if values and not stale else '—')
        self.usage_label.set_text(f'{values[1]:.1f}%' if values and not stale else '—')
        temp = self.latest.get('temperature')
        self.temp_label.set_text(f'{temp:.0f}°C' if temp is not None and not stale else '—')
        self.live_button.set_label('● Live' if self.live else 'Resume live')
        if stale:
            self.status.set_text('Recorder offline · start with: systemctl --user start cpu-scope-recorder')
        else:
            days = self.latest.get('raw_days', 7)
            retention = f'{days} days' if days else 'forever'
            self.status.set_text(f'Recording 4×/s · 0.25 s: 1 hour · 1 s: {retention} · minute history: forever')

    def refresh_labels(self, redraw=True):
        start, end = datetime.fromtimestamp(self.end - self.span()), datetime.fromtimestamp(self.end)
        self.window_label.set_text(f'{start:%d %b %Y  %H:%M:%S}   —   {end:%d %b %Y  %H:%M:%S}   {"· LIVE" if self.live else "· HISTORY"}')
        self.live_button.set_label('● Live' if self.live else 'Resume live')
        self.setting_timeline = True
        first = min(time.time(), (self.extent[0] if self.extent else time.time()) + self.span())
        self.timeline.set_value(min(1, max(0, (self.end - first) / max(1, time.time() - first))))
        self.setting_timeline = False
        if redraw:
            self.chart.queue_draw()

    def request_query(self):
        if self.closed or self.future is not None or not self.dirty:
            return
        path = data_dir() / 'history.sqlite3'
        if not path.exists():
            return
        self.dirty = False
        generation = self.generation
        self.last_query = time.monotonic()
        self.future = self.pool.submit(query, path, self.end - self.span(), self.end, None if self.separate() else self.cpu, average_seconds=self.average_seconds)
        self.future.add_done_callback(lambda future: GLib.idle_add(self.apply_query, future, generation))

    def apply_query(self, future, generation):
        self.future = None
        if self.closed:
            return False
        try:
            points, level, step, extent = future.result()
            if generation == self.generation:
                self.points, self.step, self.extent = points, step, extent
                if self.separate():
                    self.series = {}
                    for t, values in points:
                        for cpu, v in values.items():
                            self.series.setdefault(cpu, []).append((t, v))
                else:
                    self.series = {self.cpu: points}
                self.update_legend()
                resolution = {0.25: '0.25 s', 1: '1 s', 60: '1 min', 3600: '1 h', 86400: '1 day'}[level]
                effective = f'{self.average_seconds:g} s'
                if step > self.average_seconds:
                    effective += f' (effective {step:g} s)'
                self.average_label.set_text(effective)
                self.average_label.set_tooltip_text(f'Stored samples: {resolution}. Wider windows and older history require coarser averaging.')
                key = 'Colored lines: each CPU · Hover: nearest CPU' if self.separate() else 'Line: mean · Band: min–max'
                self.detail_label.set_text(f'{step:g} s average · {key} · Scroll/drag: pan · Ctrl+scroll: zoom')
                self.refresh_labels()
        except Exception as exc:
            self.status.set_text(f'History unavailable: {exc}')
        self.request_query()
        return False

    def refresh_readings(self):
        if self.closed:
            return False
        self.update_stress()
        try:
            self.latest = json.loads((runtime_dir() / 'latest.json').read_text())
        except (OSError, ValueError):
            pass
        self.update_live()
        return True

    def tick(self):
        if self.closed:
            return False
        if self.live:
            self.end = time.time()
            if time.monotonic() - self.last_query >= self.refresh_seconds - .05:
                self.dirty = True
            self.refresh_labels(redraw=False)
        self.request_query()
        return True


class Application(Adw.Application):
    def __init__(self, smoke=False):
        super().__init__(application_id='io.local.CpuScope')
        self.smoke = smoke
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, self.terminate)
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, self.terminate)

    def terminate(self):
        window = self.get_active_window()
        if window:
            window.close()
        self.quit()
        return False

    def do_activate(self):
        window = self.get_active_window()
        if window is None:
            Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            Gtk.Settings.get_default().set_property('gtk-enable-animations', False)
            provider = Gtk.CssProvider()
            provider.load_from_data(CSS)
            Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            window = Window(self)
        window.present()
        if self.smoke:
            def exercise():
                window.range_widget.set_selected(6)
                window.pan(-.8)
                window.date_entry.set_text('2000-01-01 00:00')
                window.jump(window.date_entry)
                if 0 in window.rows:
                    window.core_list.select_row(window.rows[0][0])
                window.go_live()
                if -1 in window.rows:
                    window.core_list.select_row(window.rows[-1][0])
                window.mode_widget.set_selected(1)
                window.range_widget.set_selected(1)
                return False
            GLib.timeout_add(2000, exercise)
            GLib.timeout_add(5000, lambda: (window.close(), False)[1])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke-test', action='store_true')
    args = parser.parse_args()
    Application(args.smoke_test).run([])
