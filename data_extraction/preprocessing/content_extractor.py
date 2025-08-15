import requests
from bs4 import BeautifulSoup
from newspaper import Article

def extract_content_from_link(link):
    try:
        article = Article(link)
        article.download()
        article.parse()
        if article.text.strip():
            return article.text.strip()
    except Exception:
        pass
    try:
        response = requests.get(link, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        return soup.body.get_text(separator="\n", strip=True) if soup.body else ""
    except Exception as e:
        return f"Error fetching content: {e}"