import os
import re
import json
from datetime import datetime
from flask import Flask, render_template, abort, jsonify
from bs4 import BeautifulSoup

app = Flask(__name__)

# ---------- برندینگ ----------
@app.context_processor
def inject_brand():
    return {
        "brand": "AvaNews",
        "brand_tagline": "آخرین اخبار و داغ‌ترین‌ها",
    }

# ---------- مسیرها (قابل تنظیم با Environment Variables) ----------
NEWS_DIR = os.environ.get("NEWS_DIR", "news")
VIEWS_FILE = os.environ.get("VIEWS_FILE", "views.json")

os.makedirs(NEWS_DIR, exist_ok=True)

# ---------- مدیریت بازدیدها ----------
def load_views():
    if os.path.exists(VIEWS_FILE):
        try:
            with open(VIEWS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_views(views):
    try:
        with open(VIEWS_FILE, "w", encoding="utf-8") as f:
            json.dump(views, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"خطا در ذخیره بازدیدها: {e}")

def increment_view(slug):
    views = load_views()
    views[slug] = views.get(slug, 0) + 1
    save_views(views)
    return views[slug]

# ---------- پارس کردن فایل خبر ----------
def parse_news_file(filename):
    path = os.path.join(NEWS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    soup = BeautifulSoup(raw, "html.parser")

    title = filename
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        title = h1.get_text(strip=True)
    elif soup.title and soup.title.string:
        title = soup.title.string.strip()

    p = soup.find("p")
    summary = p.get_text(strip=True) if p else ""

    img = soup.find("img")
    image = None
    if img and img.has_attr("src"):
        image = img["src"]

    m = re.match(r"(\d{4}-\d{2}-\d{2})", filename)
    if m:
        try:
            date = datetime.strptime(m.group(1), "%Y-%m-%d")
        except ValueError:
            date = datetime.fromtimestamp(os.path.getmtime(path))
    else:
        date = datetime.fromtimestamp(os.path.getmtime(path))

    return {
        "slug": filename[:-5] if filename.endswith(".html") else filename,
        "filename": filename,
        "title": title,
        "summary": summary,
        "image": image,
        "date": date,
        "date_str": date.strftime("%Y/%m/%d"),
        "content": str(soup.body) if soup.body else str(soup),
    }

# ---------- گرفتن همه اخبار ----------
def get_all_news():
    if not os.path.exists(NEWS_DIR):
        return []
    files = [f for f in os.listdir(NEWS_DIR) if f.endswith(".html")]
    news_list = []
    for f in files:
        try:
            news_list.append(parse_news_file(f))
        except Exception as e:
            print(f"خطا در پارس {f}: {e}")
    news_list.sort(key=lambda x: x["date"], reverse=True)
    return news_list

# ---------- محاسبه اخبار داغ ----------
def get_hot_news(news_list, views, limit=5):
    hot = sorted(
        news_list,
        key=lambda n: views.get(n["slug"], 0),
        reverse=True
    )[:limit]
    return [n for n in hot if views.get(n["slug"], 0) > 0]

# ---------- روت‌ها ----------
@app.route("/")
def index():
    news_list = get_all_news()
    views = load_views()
    hot_news = get_hot_news(news_list, views)
    return render_template(
        "index.html",
        news_list=news_list,
        hot_news=hot_news,
        views=views,
    )

@app.route("/news/<slug>")
def news_detail(slug):
    if "/" in slug or "\\" in slug or ".." in slug:
        abort(404)

    filename = slug + ".html"
    path = os.path.join(NEWS_DIR, filename)
    if not os.path.exists(path):
        abort(404)

    news = parse_news_file(filename)
    view_count = increment_view(slug)

    news_list = get_all_news()
    views = load_views()
    hot_news = get_hot_news(news_list, views)

    return render_template(
        "news.html",
        news=news,
        view_count=view_count,
        hot_news=hot_news,
        views=views,
    )

# ---------- API ----------
@app.route("/api/news")
def api_news():
    news_list = get_all_news()
    return jsonify([
        {
            "slug": n["slug"],
            "title": n["title"],
            "summary": n["summary"],
            "image": n["image"],
            "date": n["date_str"],
        }
        for n in news_list
    ])

@app.route("/api/hot")
def api_hot():
    news_list = get_all_news()
    views = load_views()
    hot = get_hot_news(news_list, views)
    return jsonify([
        {
            "slug": n["slug"],
            "title": n["title"],
            "views": views.get(n["slug"], 0),
        }
        for n in hot
    ])

@app.route("/health")
def health():
    return {"status": "ok"}, 200

# ---------- اجرا ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
