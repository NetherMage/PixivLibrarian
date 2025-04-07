from pixivpy3 import AppPixivAPI, ByPassSniApi
from SearchUtil import SearchUtil

# APP CONFIGURATIONS #
LIBRARY_ROOT_URL = "D:/Storage/C/Pictures/Pics"
#LIBRARY_ROOT_URL = "C:/Desktop Stuff Local/PixivLibrarian/illust"
PIXIV_REFRESH_TOKEN = "aHc9BtLWVpWpNVPN91LbxLBOY268v6k0nu2kRAUfTeg" # Run 'gppt login' in CLI to get the token
DANBOORU_COOKIE = "_danbooru2_session=Q14fdiZXGt8JE4qHhZuo7YAexnmfKpCizxU10ytjvAyuVM0QtwTjFzUfEkogRsOHAEdzD%2BqrCS8eDOLCMSXmS3jC79ez%2FU6OHDwVJGvu2q8omFHOuwvB9O2f8K8AEJ2M5BxAj2JVW1yVSO1tuqArBszxH4y5nI8xo3zMaHICvsJ6ly9A5QL%2Fc9ePDXEKFb5EV91cm0%2FU0ey1zDQEn1TAQpP2LA7O0bB9CnPlnROijrvHr%2FyJpgWQyiSckRXms9XbuNFiGOweZ0WQ4lwMe%2BJ38T7Nas7tlBxnNlTXugXrOYMs%2FDCuq9%2B9yn9%2FNIuTH9dqBECQMK4Sq3eFVvroG96YjivPfsGqCimq1WtaH%2FgOLpYHcpLqTp7RMpUxeJjkvUNXtXZzFA%3D%3D--NcdBC%2F6cXdIvmcn%2B--NIXSq6gpChmGIu3KOVuNZg%3D%3D"
FILE_EXT = ".jpg"

# GLOBAL VARIABLES DO NOT EDIT #
TITLE = "Illustration Librarian"
PIXIV_API = ByPassSniApi()  # bypass the GFW 
SRCH_UTIL = SearchUtil(LIBRARY_ROOT_URL)
