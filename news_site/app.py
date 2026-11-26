import os
import re
import json
from datetime import datetime
from flask import Flask, render_template, abort, jsonify
from bs4 import BeautifulSoup

app = Flask(__name__)

NEWS_DIR = "news"
VIEWS_FILE = "views.json"

# ---------- مدیریت بازدیدها ----------
def load_views():
    if os.path.exists(VIEWS_FILE):
        with open(VIEWS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_views(views):
    with open(VIEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(views, f, ensure_ascii=False, indent=2)

def increment_view(slug):
    views = load_views()
    views[slug] = views.get(slug, 0) + 1
    save_views(views)
    return views[slug]

# ---------- پارس کردن فایل خبر ----------
def parse_news_file(filename):
    path = os.path.join(NEWS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    title = soup.title.string.strip() if soup.title and soup.title.string else filename
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)

    # خلاصه: اولین پاراگراف
    p = soup.find("p")
    summary = p.get_text(strip=True) if p else ""

    # تصویر
    img = soup.find("img")
    image = img["src"] if img and img.has_attr("src") else None

    # تاریخ از نام فایل: YYYY-MM-DD-xxx.html
    m = re.match(r"(\d{4}-\d{2}-\d{2})", filename)
    if m:
        date = datetime.strptime(m.group(1), "%Y-%m-%d")
    else:
        date = datetime.fromtimestamp(os.path.getmtime(path))

    return {
        "slug": filename.replace(".html", ""),
        "filename": filename,
        "title": title,
        "summary": summary,
        "image": image,
        "date": date,
        "date_str": date.strftime("%Y/%m/%d"),
        "content": str(soup.body) if soup.body else str(soup),
    }

# ---------- گرفتن همه خبر ها ----------
def get_all_news():
    if not os.path.exists(NEWS_DIR):
        return []
    files = [f for f in os.listdir(NEWS_DIR) if f.endswith(".html")]
    news_list = [parse_news_file(f) for f in files]
    news_list.sort(key=lambda x: x["date"], reverse=True)
    return news_list

# ---------- روت ها ----------
@app.route("/")
def index():
    news_list = get_all_news()
    views = load_views()

    # اخبار داغ = 5 خبر پربازدید
    hot_news = sorted(
        news_list,
        key=lambda n: views.get(n["slug"], 0),
        reverse=True
    )[:5]
    # فیلتر خبرهایی که حداقل یک بازدید دارند
    hot_news = [n for n in hot_news if views.get(n["slug"], 0) > 0]

    return render_template(
        "index.html",
        news_list=news_list,
        hot_news=hot_news,
        views=views,
    )


@app.route("/news/<slug>")
def news_detail(slug):
    filename = slug + ".html"
    path = os.path.join(NEWS_DIR, filename)
    if not os.path.exists(path):
        abort(404)

    news = parse_news_file(filename)
    view_count = increment_view(slug)
    news_list = get_all_news()
    views = load_views()

    hot_news = sorted(
        news_list,
        key=lambda n: views.get(n["slug"], 0),
        reverse=True
    )[:5]
    hot_news = [n for n in hot_news if views.get(n["slug"], 0) > 0]

    return render_template(
        "news.html",
        news=news,
        view_count=view_count,
        hot_news=hot_news,
        views=views,
    )


# ---------- API برای AJAX (اختیاری) ----------
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
    hot = sorted(news_list, key=lambda n: views.get(n["slug"], 0), reverse=True)[:5]
    hot = [n for n in hot if views.get(n["slug"], 0) > 0]
    return jsonify([
        {
            "slug": n["slug"],
            "title": n["title"],
            "views": views.get(n["slug"], 0),
        }
        for n in hot
    ])


if __name__ == "__main__":
    app.run(debug=True)