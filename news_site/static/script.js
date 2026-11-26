// ---- بروزرسانی خودکار اخبار داغ هر 30 ثانیه ----
async function refreshHotNews() {
    try {
        const res = await fetch('/api/hot');
        const hot = await res.json();
        const list = document.getElementById('hotList');
        if (!list) return;

        if (hot.length === 0) {
            list.innerHTML = '<li class="empty">هنوز خبر داغی وجود ندارد</li>';
            return;
        }

        list.innerHTML = hot.map((h, i) => `
            <li>
                <a href="/news/${h.slug}">
                    <span class="hot-badge">${i + 1}</span>
                    <span class="hot-text">${h.title}</span>
                    <span class="hot-views">👁 ${h.views}</span>
                </a>
            </li>
        `).join('');
    } catch (e) {
        console.error('خطا در بروزرسانی اخبار داغ:', e);
    }
}

// ---- انیمیشن ورود کارت‌ها + عنوان داینامیک ----
document.addEventListener('DOMContentLoaded', () => {
    // برندینگ: عنوان تب را با AvaNews هماهنگ کن
    if (!document.title.includes('AvaNews')) {
        document.title = 'AvaNews | ' + document.title;
    }

    // انیمیشن ورود کارت‌ها
    const cards = document.querySelectorAll('.news-card');
    cards.forEach((card, i) => {
        card.style.opacity = 0;
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = 1;
            card.style.transform = 'translateY(0)';
        }, i * 80);
    });

    // بروزرسانی دوره‌ای اخبار داغ
    setInterval(refreshHotNews, 30000);
});
