-- =========================
-- Drop and recreate schema
-- =========================
--DROP SCHEMA public CASCADE; -- do not uncomment this as it removes extensions
-- This is a destructive operation and should be used with caution.
--CREATE SCHEMA public;

-- =========================
-- USERS TABLE
-- =========================
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    sex TEXT,
    occupation TEXT,
    industry TEXT
);

-- =========================
-- VIEWS TABLE
-- =========================
CREATE TABLE views (
    view_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT
);

-- =========================
-- VIEW CATEGORIES (1-to-many)
-- =========================
CREATE TABLE view_categories (
    id SERIAL PRIMARY KEY,
    view_id INT REFERENCES views(view_id) ON DELETE CASCADE,
    category TEXT NOT NULL
);

-- =========================
-- MAIN ARTICLES TABLE
-- =========================
CREATE TABLE articles (
    guid TEXT PRIMARY KEY,
    title TEXT,
    link TEXT,
    published TIMESTAMPTZ,
    summary TEXT,
    description TEXT,
    image_url TEXT,
    author TEXT,
    source TEXT,
    content TEXT,
    likes INT DEFAULT 0,
    views INT DEFAULT 0,
    rating TEXT,
    difficulty TEXT,
    embedding vector(384)  -- Add embedding for recommendation
);

-- =========================
-- RSS CATEGORIES (1-to-many)
-- =========================
CREATE TABLE rss_categories (
    id SERIAL PRIMARY KEY,
    article_guid TEXT REFERENCES articles(guid) ON DELETE CASCADE,
    category TEXT
);

-- =========================
-- CATEGORIES (1-to-many, with score)
-- =========================
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    article_guid TEXT REFERENCES articles(guid) ON DELETE CASCADE,
    category TEXT,
    score FLOAT
);

-- =========================
-- TAGS (1-to-many, flat list)
-- =========================
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    article_guid TEXT REFERENCES articles(guid) ON DELETE CASCADE,
    tag TEXT
);

-- =========================
-- LLM CONTENT (1-to-1)
-- =========================
CREATE TABLE llm_content (
    article_guid TEXT PRIMARY KEY REFERENCES articles(guid) ON DELETE CASCADE,
    title TEXT,
    content TEXT
);
