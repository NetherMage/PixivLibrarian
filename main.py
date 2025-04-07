import os
import sys
import re
import queue
from threading import Thread
from time import sleep

import config
import json
import requests

import kivy

from Row import Row

from kivy.app import App
from kivy.core.window import Window
from KivyOnTop import register_topmost

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import partial
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.popup import Popup

from SearchModal import Search

kivy.require('1.0.7')
sys.dont_write_bytecode = True

TITLE = config.TITLE
library_root_url = config.LIBRARY_ROOT_URL
pixiv_refresh_token = config.PIXIV_REFRESH_TOKEN
pixiv_api = config.PIXIV_API
ext = config.FILE_EXT
danbooru_cookie = config.DANBOORU_COOKIE

class MainApp(App):

    def __init__(self):
        super().__init__()
        Window.bind(on_request_close=self.exit_check)
        
        # Pixiv API authentication
        pixiv_api.require_appapi_hosts()
        pixiv_api.auth(refresh_token=pixiv_refresh_token)

        self.rows = []
        self.count = 0

    def on_start(self, *args):
        Window.set_title(TITLE)

        # Register top-most
        register_topmost(Window, TITLE)
        
    def validate_inputs(self):
        # -1 would be the first item of the row from left, i.e. the count label
        # -6 would be the sixth item of the row from left, i.e. the directory spinner
        # name_texts are all under the third item(BoxLayout), and have three
        # text input, and the text labels as its children
        for row in self.rows:
            url = row.children[-2].text.strip()
            name_1 = row.children[-3].children[-1].text.strip()
            name_2 = row.children[-3].children[-3].text.strip()
            name_3 = row.children[-3].children[-5].text.strip()
            
            if not url:
                print("ERROR: URL must not be empty.")
                return False
                
            if not self.is_valid_url(url):
                print(f"ERROR: Invalid URL: {url}")
                return False

        return True
            
    def is_valid_url(self, url):
        return re.match(r'^https?://(?:www\.)?.+$', url) is not None

    def fetch_image(self, url, filepath, site_type):
        print(url)
        # Set up the session with a custom user agent
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 OPR/112.0.0.0"
        })

        # Common headers for both Pixiv and Danbooru
        headers = {
            "accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=1, i",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Opera GX";v="112"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "image",
            "sec-fetch-mode": "no-cors",
            "sec-fetch-site": "cross-site"
        }

        # Add site-specific headers
        if site_type == "pixiv":
            headers.update({
                "referer": "https://www.pixiv.net/",
                "authority": "i.pximg.net"
            })
        elif site_type == "danbooru":
            headers.update({
                "User-Agent": "my-agent",
                "referer": "https://danbooru.donmai.us/",
                #"cookie": danbooru_cookie,  # Replace with actual session cookie if needed
                "sec-fetch-site": "same-site",
                "authority": "cdn.donmai.us"
            })

        # Fetch the image
        response = session.get(url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            print("Image downloaded, writing to file.")
            # Save the image to the specified file path
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print('Image successfully downloaded!')
        else:
            print(f'Failed to fetch image. Status code: {response.status_code}')

    def start_download(self):
        row_queue = []

        print(self.rows)
        for row in self.rows:
            if row.status in ['idle', 'error']:
                row.update_status('download')
                row_queue.append(row)

        try:
            print("========STARTING DOWNLOAD========")
            for i, row in enumerate(row_queue):
                url_type = row.get_url_type()
                if url_type == 'pixiv':
                    row.update_status('success') if self.download_pixiv(row) else row.update_status('error')
                elif url_type == 'danbooru':
                    row.update_status('success') if self.download_danbooru(row) else row.update_status('error')
                elif url_type == 'twitter':
                    row.update_status('success') if self.download_twitter(row) else row.update_status('error')
                else:
                    row.update_status('error')
                    raise Exception(f"Unknown URL type during download for {row.count}: {row.get_url()}") 

            print("=======DOWNLOAD FINISHED========")

        except Exception as e:
            print("Download aborted due to: ")
            print(e)

    def download_pixiv(self, row):
        # Get the details
        try:
            artwork_id = row.get_artwork_id()
            illust = row.get_pixiv_detail()
            page_count = illust.page_count
            name = row.get_name()
            path = row.get_abspath()

            print(f"Processing {name}: {page_count}pg")

            if page_count > 1:
                # Is multipage
                dl_format_string = row.get_dl_format()
                for page in range(page_count):
                    image_url = illust.meta_pages[page].image_urls.original
                    page_name = f"{illust.user.name} - {illust.title}({artwork_id})_p{page}{ext}"
                    # Since each page title is reconstructed here, had to call the function like this way
                    formatted_page_name = row.replace_invalid_characters(page_name)
                    self.fetch_image(image_url, f"{path}\\{formatted_page_name}", 'pixiv')
                    # pixiv_api.download(image_url,
                    # path=path,
                    # name=page_name,
                    # referer=pxreferer)            
            else:
                # Is single page
                image_url = illust.meta_single_page.get("original_image_url", illust.image_urls.original)
                print("IMAGE:" + image_url)
                # pixiv_api.download(image_url,
                # path=path,
                # name=name,
                # referer=pxreferer)
                self.fetch_image(image_url, f"{path}\\{name}", 'pixiv')
                print("OK.. " + name + " completed.\n");

            pixiv_api.illust_bookmark_add(artwork_id)
            return True # success
        except Exception as e:
            print("Download aborted due to: ")
            print(e)
            return False # fail

    def download_danbooru(self, row):
        try:
            # Modify the post URL to point to the JSON endpoint
            post_id = row.get_url().split('/')[-1]
            json_url = f"https://danbooru.donmai.us/posts/{post_id}.json"
            filepath = f"{row.get_abspath()}\\{row.get_name()}"
            
            # Send a GET request to fetch the JSON data
            response = requests.get(json_url)
            
            if response.status_code == 200:
                # Parse the JSON response
                post_data = response.json()
                
                # Extract the original image URL
                image_url = post_data.get("file_url")
                
                if image_url:
                    self.fetch_image(image_url, filepath + ext, 'danbooru')
                    return True # success
                else:
                    raise("Original image URL not found.")
                return False # fail
        except Exception as e:
            print("Download aborted due to: ")
            print(e)
            return False # fail

    def download_twitter(self, tweet_id):
        try:
            #TODO: Unimplemented as Twitter API cost money
            pass
        except Exception as e:
            print("Download aborted due to: ")
            print(e)
            return False  # fail

    def thread_download(self):
        download = Thread(target=self.start_download)
        download.start()
                  
    def add_row(self):
        vp_height = self.root.ids.scroll.viewport_size[1]
        sv_height = self.root.ids.scroll.height

        new_row = Row(
            count=self.count,
            # If there is a previous row, inherit its picked subdirectory
            last_library=self.rows[-1].children[-5].text if self.rows else "",
            remove_row_callback=self.remove_row
        )
        
        self.rows.append(new_row)
        self.root.ids.rows.add_widget(new_row)
        
        self.count += 1

        if vp_height > sv_height:  # otherwise there is no scrolling
            # calculate y value of bottom of scrollview in the viewport
            scroll = self.root.ids.scroll.scroll_y
            bottom = scroll * (vp_height - sv_height)

            # use Clock.schedule_once because we need updated viewport height
            # this assumes that new widgets are added at the bottom
            # so the current bottom must increase by the widget height to maintain position
            Clock.schedule_once(partial(self.adjust_scroll, bottom + new_row.height), -1)

    def remove_row(self, instance):
        row_item = instance
        row_list = row_item.parent

        self.rows.remove(row_item)
        row_list.remove_widget(row_item)

    def search(self):
        search_word = self.root.ids["search_input"].text

        search_modal = Search(search_word)
        search_modal.open()

    def adjust_scroll(self, bottom, dt):
        vp_height = self.root.ids.scroll.viewport_size[1]
        sv_height = self.root.ids.scroll.height
        self.root.ids.scroll.scroll_y = bottom / (vp_height - sv_height)
        self.root.ids.scroll.scroll_y = 0 # Always scroll to bottom

    def exit_check(self, *args):
        box = BoxLayout(orientation = 'vertical', padding = (10))
        popup = Popup(title='Confirm exit?', title_size= (30), 
                      title_align = 'center', content = box,
                      size_hint=(None, None), size=(400, 200),
                      auto_dismiss = True)
                      
        box.add_widget(Button(text="Yes", on_press=lambda instance: App.get_running_app().stop()))
        box.add_widget(Button(text="No", on_press=lambda instance: popup.dismiss()))

        popup.open()
        return True

    def build(self):
        self.root = Builder.load_file('main.kv')
        return self.root

if __name__ == '__main__':

    MainApp().run()
    

    
