import json
import os
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))

ROOT = Path(__file__).resolve().parents[2]
json_path = ROOT / "data_extraction" / "content" / "content.json"


def push_to_db(data):
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )
    conn.autocommit = True
    cur = conn.cursor()

    # ----------------------
    # 1. Insert articles
    # ----------------------
    articles_values = []
    for item in data:
        articles_values.append((
            item["guid"],
            item.get("title"),
            item.get("link"),
            item.get("published"),
            item.get("summary"),
            item.get("description"),
            item.get("image_url"),
            item.get("author"),
            item.get("source"),
            item.get("content"),
            item.get("likes", 0),
            item.get("views", 0),
            item.get("rating"),
            item.get("difficulty")
        ))

    article_query = """
        INSERT INTO articles (
            guid, title, link, published, summary, description, image_url,
            author, source, content, likes, views, rating, difficulty
        ) VALUES %s
        ON CONFLICT (guid) DO NOTHING;
    """
    execute_values(cur, article_query, articles_values)

    # ----------------------
    # 2. Insert RSS categories
    # ----------------------
    rss_values = []
    for item in data:
        for cat in item.get("rss_categories", []):
            rss_values.append((item["guid"], cat))

    rss_query = """
        INSERT INTO rss_categories (article_guid, category)
        VALUES %s
        ON CONFLICT DO NOTHING;
    """
    if rss_values:
        execute_values(cur, rss_query, rss_values)

    # ----------------------
    # 3. Insert categories (with score)
    # ----------------------
    cat_values = []
    for item in data:
        for cat_obj in item.get("categories", []):
            cat_values.append((item["guid"], cat_obj["category"], cat_obj["score"]))

    cat_query = """
        INSERT INTO categories (article_guid, category, score)
        VALUES %s
        ON CONFLICT DO NOTHING;
    """
    if cat_values:
        execute_values(cur, cat_query, cat_values)

    # ----------------------
    # 4. Insert tags
    # ----------------------
    tag_values = []
    for item in data:
        for tag in item.get("tags", []):
            tag_values.append((item["guid"], tag))

    tag_query = """
        INSERT INTO tags (article_guid, tag)
        VALUES %s
        ON CONFLICT DO NOTHING;
    """
    if tag_values:
        execute_values(cur, tag_query, tag_values)

    # ----------------------
    # 5. Insert LLM_CONTENT
    # ----------------------
    llm_values = []
    for item in data:
        llm = item.get("LLM_CONTENT")
        if llm:
            llm_values.append((item["guid"], llm.get("title"), llm.get("content")))

    llm_query = """
        INSERT INTO llm_content (article_guid, title, content)
        VALUES %s
        ON CONFLICT (article_guid) DO NOTHING;
    """
    if llm_values:
        execute_values(cur, llm_query, llm_values)

    cur.close()
    conn.close()
    print(f"Pushed {len(data)} articles to DB successfully.")


def main():
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    push_to_db(data)


if __name__ == "__main__":
    main()
