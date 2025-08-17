import sys
import json
import psycopg2
from psycopg2.extras import Json
from dateutil import parser as dateparser

from pathlib import Path

from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, EMBED_MODEL
from embed import embed_text

def connect():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def parse_published(value):
    if not value:
        return None
    try:
        dt = dateparser.parse(value)
        return dt
    except Exception:
        return None

def text_for_embedding(article: dict) -> str:
    title = article.get("title") or ""
    content = article.get("content") or article.get("summary") or ""
    # Truncate excessively long content to keep embedding fast
    blob = f"{title} \n\n {content}"
    return blob[:5000]

def insert_article(cur, article: dict, embedding: list):
    cur.execute(
        '''
        INSERT INTO contents
        (guid, title, link, published, summary, description, image_url, author, source, content,
         rss_categories, categories, llm_content, likes, views, embedding)
        VALUES
        (%(guid)s, %(title)s, %(link)s, %(published)s, %(summary)s, %(description)s, %(image_url)s,
         %(author)s, %(source)s, %(content)s, %(rss_categories)s, %(categories)s, %(llm_content)s,
         %(likes)s, %(views)s, %(embedding)s)
        ON CONFLICT (guid) DO UPDATE SET
            title = EXCLUDED.title,
            link = EXCLUDED.link,
            published = EXCLUDED.published,
            summary = EXCLUDED.summary,
            description = EXCLUDED.description,
            image_url = EXCLUDED.image_url,
            author = EXCLUDED.author,
            source = EXCLUDED.source,
            content = EXCLUDED.content,
            rss_categories = EXCLUDED.rss_categories,
            categories = EXCLUDED.categories,
            llm_content = EXCLUDED.llm_content,
            likes = COALESCE(EXCLUDED.likes, contents.likes),
            views = COALESCE(EXCLUDED.views, contents.views),
            embedding = EXCLUDED.embedding;
        ''',
        {
            "guid": article.get("guid"),
            "title": article.get("title"),
            "link": article.get("link"),
            "published": parse_published(article.get("published")),
            "summary": article.get("summary"),
            "description": article.get("description"),
            "image_url": article.get("image_url"),
            "author": article.get("author"),
            "source": article.get("source"),
            "content": article.get("content"),
            "rss_categories": Json(article.get("rss_categories")) if article.get("rss_categories") is not None else None,
            "categories": Json(article.get("categories")) if article.get("categories") is not None else None,
            "llm_content": Json(article.get("LLM_CONTENT")) if article.get("LLM_CONTENT") is not None else None,
            "likes": article.get("likes", 0),
            "views": article.get("views", 0),
            "embedding": embedding
        }
    )

def main():
    if len(sys.argv) < 2:
        print("Usage: python app/load_content.py /path/to/content.json")
        sys.exit(1)

    json_path = Path(sys.argv[1]).expanduser().resolve()
    if not json_path.exists():
        print(f"File not found: {json_path}")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("Error: JSON must be a list of article dicts.")
        sys.exit(1)

    conn = connect()
    cur = conn.cursor()

    # Process & insert
    count = 0
    for article in data:
        blob = text_for_embedding(article)
        emb = embed_text(blob, EMBED_MODEL)
        try:
            insert_article(cur, article, emb)
            count += 1
        except Exception as e:
            print(f"Failed to insert guid={article.get('guid')}: {e}")
            conn.rollback()
        else:
            conn.commit()

    cur.close()
    conn.close()
    print(f"""✅ Done. Inserted/updated {count} articles.""")

if __name__ == "__main__":
    main()
