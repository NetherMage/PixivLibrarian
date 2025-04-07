from bs4 import BeautifulSoup
import requests


def scrape_twitter_image(tweet_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(tweet_url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find all image tags (usually under meta tags for Twitter)
        meta_tags = soup.find_all("meta", property="og:image")
        image_urls = [tag["content"] for tag in meta_tags if "content" in tag.attrs]
        print(response.text)
        return image_urls
    else:
        print(f"Failed to scrape the tweet. Status code: {response.status_code}")
        return None

# Example usage
tweet_url = "https://x.com/nevercrymoon/status/1860701662652064139"
image_urls = scrape_twitter_image(tweet_url)

if image_urls:
    print("Images found:")
    for url in image_urls:
        print(url)
