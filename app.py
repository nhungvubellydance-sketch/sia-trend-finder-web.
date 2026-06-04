import json
import time
import re
import google.generativeai as genai
import yt_dlp
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import os

app = Flask(__name__)

def search_youtube_full(keyword, max_results=50):
    """Search YouTube and get full video details in one go"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'playlistend': max_results,
        'ignoreerrors': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(
                f'ytsearch{max_results}:{keyword}',
                download=False
            )
            if results is None:
                return []
            entries = results.get('entries', [])
            return [e for e in entries if e is not None]
    except Exception as e:
        print(f"Search error: {e}")
        return []

def format_number(n):
    if n is None:
        return "N/A"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)

def get_relative_time(upload_date):
    if not upload_date or len(upload_date) != 8:
        return "N/A"
    try:
        dt = datetime.strptime(upload_date, "%Y%m%d")
        now = datetime.now()
        days = (now - dt).days
        if days == 0:
            return "Hôm nay"
        elif days < 30:
            return f"{days} ngày trước"
        elif days < 365:
            months = days // 30
            return f"{months} tháng trước"
        else:
            years = days // 365
            return f"{years} năm trước"
    except:
        return "N/A"

def remix_titles_ai(titles, api_key):
    """Use Gemini to generate remix title suggestions"""
    if not api_key:
        return [], "Vui lòng nhập API Key"
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        titles_text = "\n".join([f"- {t}" for t in titles[:10]])
        
        prompt = f"""Dưới đây là các tiêu đề video trending trên YouTube.
Với mỗi tiêu đề, hãy tạo 2 bản remix theo quy tắc 80/20 (giữ 80% tiêu đề gốc, thay đổi 20%).
Trả lời CHÍNH XÁC theo format JSON array sau (không giải thích gì thêm):
[
  {{"original": "tiêu đề gốc", "remix1": "bản remix 1", "remix2": "bản remix 2"}}
]

Các tiêu đề:
{titles_text}"""
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group()), None
        return [], "AI không trả về đúng định dạng"
    except Exception as e:
        print(f"AI remix error: {e}")
        return [], str(e)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/search', methods=['POST'])
def api_search():
    data = request.json
    keyword = data.get('keyword', '')
    min_views = data.get('min_views', 1000)
    
    if not keyword:
        return jsonify({"error": "Vui lòng nhập từ khóa"}), 400
    
    print(f"\n{'='*50}")
    print(f"🔍 Tìm kiếm: '{keyword}' (min views: {format_number(min_views)})")
    print(f"{'='*50}")
    
    all_videos = search_youtube_full(keyword, max_results=50)
    print(f"📦 yt-dlp trả về {len(all_videos)} video")
    
    if not all_videos:
        return jsonify({"error": "Không tìm thấy video nào. Thử từ khóa khác nhé!"}), 404
    
    results = []
    one_year_ago = datetime.now() - timedelta(days=365)
    
    for v in all_videos:
        title = v.get('title', 'N/A')
        view_count = v.get('view_count') or 0
        upload_date = v.get('upload_date', '')
        channel_subs = v.get('channel_follower_count') or 0
        video_id = v.get('id', '')
        
        within_year = True
        if upload_date:
            try:
                upload_dt = datetime.strptime(upload_date, "%Y%m%d")
                if upload_dt < one_year_ago:
                    within_year = False
            except:
                pass
        
        has_enough_views = view_count >= min_views
        
        if not has_enough_views:
            status = f"⏭️ Bỏ qua (views: {format_number(view_count)})"
            print(f"  [--] {title[:60]:60s} | {status}")
            continue
        elif not within_year:
            status = f"⏭️ Bỏ qua (cũ: {upload_date})"
            print(f"  [--] {title[:60]:60s} | {status}")
            continue
        else:
            status = "✅ Mới + views cao"
        
        is_jackpot = view_count > channel_subs and channel_subs > 0
        if is_jackpot:
            status += " 🏆 JACKPOT!"
        
        results.append({
            "title": title,
            "video_id": video_id,
            "url": f"https://youtube.com/watch?v={video_id}",
            "views": view_count,
            "views_formatted": format_number(view_count),
            "subscribers": channel_subs,
            "subscribers_formatted": format_number(channel_subs),
            "channel": v.get('channel', v.get('uploader', 'N/A')),
            "upload_date": upload_date,
            "upload_date_formatted": f"{upload_date[6:8]}/{upload_date[4:6]}/{upload_date[:4]}" if len(upload_date) == 8 else "N/A",
            "relative_time": get_relative_time(upload_date),
            "is_jackpot": is_jackpot,
            "within_year": within_year,
            "thumbnail": v.get('thumbnail') or f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            "duration": v.get('duration_string', 'N/A'),
        })
        
        print(f"  [{len(results):2d}] {title[:60]:60s} | {status}")
    
    results.sort(key=lambda x: x['views'], reverse=True)
    
    print(f"\n✅ Tổng kết: {len(results)} video phù hợp tiêu chí SIA")
    return jsonify({"results": results, "count": len(results)})


@app.route('/api/remix', methods=['POST'])
def api_remix():
    data = request.json
    titles = data.get('titles', [])
    api_key = data.get('api_key', '')
    
    if not titles:
        return jsonify({"error": "Không có tiêu đề"}), 400
        
    if not api_key:
        return jsonify({"error": "Vui lòng cung cấp Gemini API Key"}), 400
    
    print(f"\n🤖 AI Remix cho {len(titles)} tiêu đề...")
    remixes, error = remix_titles_ai(titles, api_key)
    
    if error:
        return jsonify({"error": error, "remixes": []})
        
    print(f"   → Tạo được {len(remixes)} bản remix")
    return jsonify({"remixes": remixes})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*50)
    print("SIA Trend Finder Web Version")
    print(f"Server is running on port {port}")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=port, threaded=True)
