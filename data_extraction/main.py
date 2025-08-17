import time
from preprocessing.rss_fetcher import load_rss_urls, fetch_rss_entries
from preprocessing.content_extractor import extract_content_from_link
from preprocessing.category_loader import load_categories
from preprocessing.nlp_classifier import classify_content
from preprocessing.article_store import load_existing_articles, save_articles_to_file
from preprocessing.createLLMContent import send_to_gemini 
from preprocessing.push_to_db import push_to_db, get_existing_guids_from_db
import json
import re

def extract_image_url(entry):
    import re

    # Helper: Find first image URL in a string (jpg, jpeg, png, gif, webp, svg)
    def find_image_url(text):
        # Regex for common image extensions
        match = re.search(r'(https?://[^\s"\'>]+?\.(?:jpg|jpeg|png|gif|webp|svg))', text, re.IGNORECASE)
        return match.group(1) if match else None

    # 1. Check description
    description = entry.get("description", "")
    url = find_image_url(description)
    if url:
        return url

    # 2. Check content:encoded
    content_encoded = entry.get("content:encoded", "")
    url = find_image_url(content_encoded)
    if url:
        return url

    # 3. Check summary
    summary = entry.get("summary", "")
    url = find_image_url(summary)
    if url:
        return url

    # 4. Check enclosure(s)
    enclosure = entry.get("enclosure")
    if enclosure and isinstance(enclosure, dict):
        url = enclosure.get("url")
        if url and re.search(r'\.(jpg|jpeg|png|gif|webp|svg)$', url, re.IGNORECASE):
            return url
    enclosures = entry.get("enclosures")
    if enclosures and isinstance(enclosures, list):
        for enc in enclosures:
            url = enc.get("url")
            if url and re.search(r'\.(jpg|jpeg|png|gif|webp|svg)$', url, re.IGNORECASE):
                return url

    # 5. Check media:content
    media_content = entry.get("media_content")
    if media_content and isinstance(media_content, list):
        for media in media_content:
            url = media.get("url")
            if url and re.search(r'\.(jpg|jpeg|png|gif|webp|svg)$', url, re.IGNORECASE):
                return url

    # 6. Check all entry values for image URLs (last resort)
    for value in entry.values():
        if isinstance(value, str):
            url = find_image_url(value)
            if url:
                return url
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    for v in item.values():
                        if isinstance(v, str):
                            url = find_image_url(v)
                            if url:
                                return url

    return None

if __name__ == "__main__":
    start_time = time.time()
    RSS_URLS = load_rss_urls()
    CATEGORIES = load_categories()
    # all_existing_articles = load_existing_articles()  # Remove this line
    # existing_guids = set(article["guid"] for article in all_existing_articles)  # Remove this line

    # Get existing GUIDs from the database instead of JSON file
    existing_guids = set(get_existing_guids_from_db())

    total_new_articles = []
    articles_to_push = []

    ind = 2
    for url in RSS_URLS:
        print(f"Fetching data from {url}...")
        entries = fetch_rss_entries(url)
        for entry in entries:
            guid = entry.get("id") or entry.get("guid") or entry.get("link")
            link = entry.get("link")
            source = url
            if not guid or not link or not source or guid in existing_guids:
                print("HHHHHHHHHHHHHHHHHHH")
                continue
            if ind > 10:
                break
            ind += 1
            print(f"Processing article: {guid}\n")
            description = entry.get("description", "")
            image_url = extract_image_url(entry)
            content = extract_content_from_link(link) if link else ""
            if not content or len(content) < 200:
                continue
            rss_categories = [tag.get("term", "").strip() for tag in entry.tags if tag.get("term")] if "tags" in entry else []
            title = entry.get("title", "")
            rss_cat_str = ", ".join(rss_categories) if rss_categories else title
            category_query = f"{rss_cat_str}"
            raw_categories = classify_content(category_query, CATEGORIES)
            categories = [
                {"category": cat["category"], "score": cat["score"]}
                for cat in raw_categories if cat["score"] >= 0.2
            ]
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
                "categories": categories,
                "likes": 0,
                "views": 0,
            }
            try:
                llm_content_str = send_to_gemini(article)
                match = re.search(r'```json\s*(\{.*\})\s*```', llm_content_str, re.DOTALL)
                if match:
                    llm_content_json = match.group(1)
                else:
                    match = re.search(r'(\{.*\})', llm_content_str, re.DOTALL)
                    llm_content_json = match.group(1) if match else '{}'
                llm_content_dict = json.loads(llm_content_json)

                for field in ["rating", "difficulty", "tags"]:
                    if field in llm_content_dict:
                        article[field] = llm_content_dict.pop(field)
                article["LLM_CONTENT"] = {
                    k: v for k, v in llm_content_dict.items() if k in ["title", "content"]
                }
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error generating or parsing LLM content: {e}")
                article["LLM_CONTENT"] = {}

            if article.get("LLM_CONTENT"):
                total_new_articles.append(article)
                articles_to_push.append(article)
                existing_guids.add(guid)
                # Optionally, you can still save to JSON for backup or transition
                # all_articles = all_existing_articles + total_new_articles
                # save_articles_to_file(all_articles)
            else:
                print("LLM_CONTENT is empty. Stopping execution.")
                break  # Exit the inner loop for entries

        else:
            continue  # Only reached if inner loop wasn't broken
        break  # Exit the outer loop for RSS_URLS if LLM_CONTENT was empty

    # Push all new articles to DB in one batch
    if articles_to_push:
        push_to_db(articles_to_push)

    print(f"Fetched {len(total_new_articles)} new articles.")
    elapsed = time.time() - start_time
    print(f"Time taken: {elapsed:.2f} seconds")