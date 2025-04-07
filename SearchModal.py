from functools import partial

from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

import SearchUtil

import config

import kivy
import subprocess
import os

kivy.require('1.0.7')

library_root_url = config.LIBRARY_ROOT_URL
TITLE = "Search Result"


class Search(ModalView):

    def __init__(self, *args):
        super().__init__()

        self.result_item = []
        self.last_searched = ""
        self.count = 0
        self.total_height = 50

        self.size_hint = (None, None)
        self.size = (800, 400)

        self.search_word = args[0]

        root_container = GridLayout(rows=2)
        self.add_widget(root_container)

        # Search bar at top
        search_container = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))
        self.search_input = TextInput(multiline=False, size_hint=(1, 1), text=self.search_word)
        self.search_input.bind(on_text_validate=self.search_on_enter)
        search_container.add_widget(self.search_input)

        # Search result scroll at bottom
        result_container = BoxLayout(orientation="horizontal", size_hint=(1, 0.9))
        self.result_scroll = ScrollView()
        result_container.add_widget(self.result_scroll)
        self.result_scroll_container = BoxLayout(size_hint=(1, None), orientation="vertical", height=self.total_height)
        self.result_scroll.add_widget(self.result_scroll_container)

        root_container.add_widget(search_container)
        root_container.add_widget(result_container)

        # Call to display result on creating the view
        self.search_on_enter(self.search_input)

    def search_on_enter(self, search_input):
        search_string = search_input.text

        if self.last_searched == search_string:
            #if Last searched word is same, don't re-search
            pass
        else:
            #Clear existing search results
            for old_result in self.result_item:
                self.result_scroll_container.remove_widget(old_result)
            self.result_item.clear()
            self.count = 0
            self.total_height = 50

            #Last searched term
            self.last_searched = search_string

            result = SearchUtil.search(library_root_url, search_string)
            for item in result:
                self.add_new_widget(item['filename'] + " | " + item['filedir'], item['path'])

    def add_new_widget(self, text, path):
        self.result_scroll_container.height = self.total_height
        self.total_height += 50

        vp_height = self.result_scroll.viewport_size[1]
        sv_height = self.result_scroll.height

        # add a new widget (must have preset height)
        label = Label(text=text, size_hint=(1, None), height=50, font_name="arial-unicode-ms.ttf")
        label.path = path
        label.bind(on_touch_down=self.open_path_in_explorer)
        self.result_item.append(label)

        self.result_scroll_container.add_widget(label)
        self.count += 1

        if vp_height > sv_height:  # otherwise there is no scrolling
            # calculate y value of bottom of scrollview in the viewport
            scroll = self.result_scroll.scroll_y
            bottom = scroll * (vp_height - sv_height)

            # use Clock.schedule_once because we need updated viewport height
            # this assumes that new widgets are added at the bottom
            # so the current bottom must increase by the widget height to maintain position
            Clock.schedule_once(partial(self.adjust_scroll, bottom + label.height), -1)

    def adjust_scroll(self, bottom, dt):
        vp_height = self.result_scroll.viewport_size[1]
        sv_height = self.result_scroll.height
        self.result_scroll.scroll_y = bottom / (vp_height - sv_height)

    def open_path_in_explorer(self, instance, touch):
        if instance.collide_point(*touch.pos):
            #print(str(instance.path).encode('ascii', 'replace').decode('ascii'))
            path = instance.path
            parent_folder = os.path.dirname(path)
            subprocess.Popen(f'explorer /select,"{path}"')

