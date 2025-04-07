from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.anchorlayout import AnchorLayout
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from functools import partial

import requests
import re

import config

library_root_url = config.LIBRARY_ROOT_URL
pixiv_api = config.PIXIV_API
ext = config.FILE_EXT
search_util = config.SRCH_UTIL

# Maps invalid Windows filename character to some similiar character
char_replacements = {
    '/': '／',
    '\\': '-',
    ':': '：',
    '*': '＊',
    '?': '？',
    '"': "'",
    '<': '[',
    '>': ']',
    '|': '-',
}

url_type = [None, 'pixiv', 'danbooru', 'twitter']

pixiv_url_pattern = re.compile(r'^https?://(www\.)?pixiv\.net/artworks/\d+$')
danbooru_pattern = re.compile(r'https://danbooru\.donmai\.us/posts/(\d+)')
twitter_url_pattern = re.compile(
    r'^https?://(www\.)?(twitter\.com|x\.com)/[A-Za-z0-9_]+/status/\d+$'
)


danbooru_prefix = 'danbooru_'

class Row(BoxLayout):

    def __init__(self, count, last_library, remove_row_callback, **kwargs):
        super().__init__(**kwargs)

        self.count = count
        self.remove_row_callback = remove_row_callback
        # setting text programmatically will trigger on_text event, use this flag to bypass
        self.ignore_input = False
        
        self.status = "idle"
        self.url_type = url_type[0]
        self.pixiv_detail = None # Currently unused as I cannot imagine a use case for this yet
        # all_download_directory keep tracks the entire list returned by autocomplete
        # so that user may enumerate it.
        self.all_download_directory = None
        # download_directory is the current selected one, which will fetched by main.py
        # to download images.
        self.download_directory = None
        # Index for the result list of a fuzzy search
        # -1 means reset
        self.dir_pointer = -1

        self.setup_layout(last_library)
        Clock.schedule_interval(self.update_color, 0.5)
        
    def setup_layout(self, last_library):
        self.size_hint = (1.0, None)
        self.height = 40

        count_label = Label(
            text=str(self.count),
            size_hint=(0.02, 1.0),
        )

        url_input = TextInput(multiline=False, size_hint_x=0.15)
        url_input.bind(text=self.url_input_process)

        name_label = Label(
            text="",
            size_hint=(0.15, 1.0),
        )

        dl_format_input = TextInput(multiline=False, size_hint_x=0.15)
        # TODO
        #dl_format_input.bind(text=self.input_process)

        subdir_input = TextInput(multiline=False, size_hint_x=0.15)
        subdir_input.bind(text=self.subdir_input_process)
        subdir_input.text = last_library

        del_anchor = AnchorLayout(anchor_x="right", size_hint=(0.02, 0.8))
        del_button = Button(text="×")
        del_button.bind(on_press=self.remove_row)
        del_anchor.add_widget(del_button)

        self.add_widget(count_label)
        self.add_widget(url_input)
        self.add_widget(name_label)
        self.add_widget(dl_format_input)
        self.add_widget(subdir_input)
        self.add_widget(del_anchor) 

    def set_bgcolor(self,r,b,g,o,*args):
        self.canvas.after.clear()
        with self.canvas.after:
            Color(r,g,b,o)
            self.rect = Rectangle(pos=self.children[-1].pos,size=self.children[-1].size)

        self.bind(pos=self.update_rect,
                  size=self.update_rect)
                  
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def update_color(self, *args):
        if self.status == "download":
            self.set_bgcolor(1, 0, 1, 0.3)  # Yellow
        elif self.status == "success":
            self.set_bgcolor(0, 0, 1, 0.3)  # Green
        elif self.status == "error":
            self.set_bgcolor(1, 0, 0, 0.3)  # Red
        else:
            self.set_bgcolor(1, 1, 1, 0)  # Default (White)
            
    def update_status(self, status, *args):
        self.status = status

    def remove_row(self, *args):
        self.remove_row_callback(self)

    def url_entered_pixiv(self, instance):
        # Get the file name of the illustration
        try:
            url = instance.text
            artwork_id = url.split('/')[-1]
            # Assume that main.py already done authenticating pixiv_api
            # Directly extract the illust from json
            illust = pixiv_api.illust_detail(artwork_id).illust
            formatted_title = self.replace_invalid_characters(illust.title)

            if illust.page_count > 1:
                illust_name = f"{illust.user.name} - {formatted_title}({artwork_id})_px{ext}"
            else:
                illust_name = f"{illust.user.name} - {formatted_title}({artwork_id}){ext}"

            print(f"{url} : {illust_name}")

            self.children[-3].text = illust_name
            self.url_type = url_type[1]
            self.pixiv_detail = illust
            
        except Exception as e:
            print(e)
            self.url_type = url_type[0]

    def url_entered_danbooru(self, instance):
        # Get the text (URL) from the instance
        url = instance.text
        
        # Remove everything after the '?' symbol (query parameters)
        url = url.split('?')[0]
        
        # Extract the last part of the URL path which should be the illustration ID
        # Assuming the format: https://danbooru.donmai.us/posts/8022525
        match = re.search(r'/posts/(\d+)', url)
        
        if match:
            self.children[-3].text = danbooru_prefix + match.group(1)
            self.url_type = url_type[2]
        else:
            # Handle cases where the URL format is incorrect or doesn't match
            self.children[-3].text = ""
            self.url_type = url_type[0]
            print("Invalid Danbooru URL format.")

    def url_entered_twitter(self, instance):
        # Get the text (URL) from the instance
        url = instance.text
        
        # Remove everything after the '?' symbol (query parameters)
        url = url.split('?')[0]
        
        # Extract the tweet ID using the Twitter URL pattern
        match = re.search(r'/status/(\d+)', url)
        
        if match:
            # Assuming you want to use the tweet ID for some purpose
            tweet_id = match.group(1)
            self.children[-3].text = tweet_id
            self.url_type = url_type[3] 
        else:
            self.children[-3].text = ""
            self.url_type = url_type[0]
            print("Invalid Twitter URL format.")

    def url_input_process(self, instance, text):
        stripped_text = text.strip()
        instance.text = stripped_text
        self.update_status("idle")

        if bool(pixiv_url_pattern.match(stripped_text)):
            self.url_entered_pixiv(instance)
        elif bool(danbooru_pattern.match(stripped_text)):
            self.url_entered_danbooru(instance)
        elif bool(twitter_url_pattern.match(stripped_text)):
            self.url_entered_twitter(instance) 
        else:
            # Doesn't match any known compatible URL type... error
            self.children[-3].text = ""
            self.url_type = url_type[0]

    def subdir_input_process(self, instance, text):

        if self.ignore_input:
            self.ignore_input = False
            return

        if text and self.dir_pointer == -1 and text[-1] == '\t':
            stripped_text = text.strip().replace('\r', '').replace('\n', '')
            #instance.text = stripped_text # This will get rid of the 'tab' character

            if stripped_text:
                autocomplete_result = search_util.search_dir(stripped_text)
                
                if autocomplete_result:
                    self.all_download_directory = autocomplete_result
                    self.dir_pointer = 0

                    selected_result = self.all_download_directory[self.dir_pointer]

                    self.download_directory = selected_result
                    self.ignore_input = True
                    instance.text = selected_result.rel_path
                    # Move the cursor to end, had to use Clock so that the text change took effect first
                    Clock.schedule_once(partial(instance.do_cursor_movement, 'cursor_end')) 
                else:
                    # To show that autocomplete failed, completely delete the text
                    self.ignore_input = True
                    instance.text = ""
                    self.all_download_directory = None
                    self.download_directory = None
                    dir_pointer = -1
        elif text and self.dir_pointer >= 0 and text[-1] == '\t':
            # Enumerate the autocomplete
            self.dir_pointer += 1
            if self.dir_pointer >= len(self.all_download_directory):
                self.dir_pointer = 0

            selected_result = self.all_download_directory[self.dir_pointer]

            self.download_directory = selected_result
            self.ignore_input = True
            instance.text = selected_result.rel_path
            # Move the cursor to end, had to use Clock so that the text change took effect first
            Clock.schedule_once(partial(instance.do_cursor_movement, 'cursor_end')) 
        elif not text:
            # main.py should know this mean download at root
            # TODO
            # this case is exactly same as the else case, but supposedly I wanted to use this case to handle
            # when user purposefully left it empty (to download at root), or accidentally left empty.
            self.download_directory = None
            self.dir_pointer = -1 # Reset the pointer
        else:
            # This case is triggered also if user type normally (not tabbing), thus this also help to ensure
            # next time user press tab, autocomplete case will trigger again to search with latest keywords.
            self.download_directory = None # No tab detected, and it's not empty, assumes user still typing
            self.dir_pointer = -1 # Reset the pointer

    def replace_invalid_characters(_, text):
        for char, replacement in char_replacements.items():
            text = text.replace(char, replacement)
        return text
        
    def get_name(self):
        filename = self.replace_invalid_characters(self.children[-3].text.strip())
        return filename

    def get_pixiv_detail(self):
        return self.pixiv_detail

    def get_artwork_id(self):
        url = self.get_url()
        artwork_id = url.split('/')[-1]
        return artwork_id
    
    def get_abspath(self):
        # Assuming if the path just copy pasted from other rows, try to manually construct an absolute path anyway
        return self.download_directory.abs_path if self.download_directory else f"{library_root_url}/{self.children[-5].text}"
        
    def get_url(self):
        if self.url_type == "danbooru":
            # For danbooru, let's remove the parameters
            return self.children[-2].text.split('?')[0]
        else:
            return self.children[-2].text
        
    def get_url_type(self):
        return self.url_type

    def get_dl_format(self):
        return self.children[-4].text
