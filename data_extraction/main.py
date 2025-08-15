import time
from preprocessing.rss_fetcher import load_rss_urls, fetch_rss_entries
from preprocessing.content_extractor import extract_content_from_link
from preprocessing.category_loader import load_categories
from preprocessing.nlp_classifier import classify_content
from preprocessing.article_store import load_existing_articles, save_articles_to_file

def extract_image_url(description):
    import re
    match = re.search(r'<img[^>]+src="([^"]+)"', description)
    return match.group(1) if match else None

if __name__ == "__main__":
    start_time = time.time()
    RSS_URLS = load_rss_urls()
    CATEGORIES = load_categories()
    all_existing_articles = load_existing_articles()
    existing_guids = set(article["guid"] for article in all_existing_articles)
    total_new_articles = []

    for url in RSS_URLS:
        print(f"Fetching data from {url}...")
        entries = fetch_rss_entries(url)
        for entry in entries:
            guid = entry.get("id") or entry.get("guid") or entry.get("link")
            link = entry.get("link")
            source = url
            if not guid or not link or not source or guid in existing_guids:
                continue
            description = entry.get("description", "")
            image_url = extract_image_url(description)
            content = extract_content_from_link(link) if link else ""
            if not content or len(content) < 200:
                continue
            rss_categories = [tag.get("term", "").strip() for tag in entry.tags if tag.get("term")] if "tags" in entry else []
            title = entry.get("title", "")
            rss_cat_str = ", ".join(rss_categories) if rss_categories else title
            category_query = f"{rss_cat_str}"
            categories = classify_content(category_query, CATEGORIES)
            article = {
                "guid": guid,
                "title": title,
                "link": link,
                "published": entry.get("published"),
                "summary": entry.get("summary"),
                "description": description,
                "image_url": image_url,
                "author": entry.get("author"),
                "source": source,
                "content": content,
                "rss_categories": rss_categories,
                "categories": categories
            }
            total_new_articles.append(article)
            existing_guids.add(guid)

    print(f"Fetched {len(total_new_articles)} new articles.")
    all_articles = all_existing_articles + total_new_articles
    save_articles_to_file(all_articles)
    elapsed = time.time() - start_time
    print(f"Stored {len(all_articles)} total articles in content/content.json")
    print(f"Time taken: {elapsed:.2f} seconds")