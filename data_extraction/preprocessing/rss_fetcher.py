import feedparser

def fetch_rss_entries(url):
    feed = feedparser.parse(url)
    return feed.entries

def load_rss_urls(filename="resources/rss_urls.txt"):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]