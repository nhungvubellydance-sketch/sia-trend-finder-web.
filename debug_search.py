import yt_dlp
import json
from datetime import datetime, timedelta

keyword = "manifest love"
one_year_ago = datetime.now() - timedelta(days=365)

ydl_opts = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": False,
    "playlistend": 10,
    "ignoreerrors": True,
}

print(f"Tim kiem: {keyword}")
print(f"Ngay 1 nam truoc: {one_year_ago.strftime('%Y%m%d')}")
print()

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    results = ydl.extract_info(f"ytsearch10:{keyword}", download=False)
    if results is None:
        print("LOI: yt-dlp tra ve None!")
        exit()
    entries = [e for e in results.get("entries", []) if e]
    print(f"So video tra ve: {len(entries)}")
    print()
    
    ok_count = 0
    for i, v in enumerate(entries):
        title = v.get("title", "?")
        views = v.get("view_count", 0) or 0
        subs = v.get("channel_follower_count", 0) or 0
        date = v.get("upload_date", "?")
        
        within_year = True
        if date and date != "?":
            try:
                dt = datetime.strptime(date, "%Y%m%d")
                if dt < one_year_ago:
                    within_year = False
            except:
                pass
        
        over_100k = views >= 100000
        is_jackpot = views > subs and subs > 0
        
        if not within_year:
            status = "QUA CU"
        elif not over_100k:
            status = f"IT VIEWS ({views:,})"
        else:
            status = f"OK! Jackpot={is_jackpot}"
            ok_count += 1
        
        print(f"[{i+1}] {title[:70]}")
        print(f"    Views: {views:,} | Subs: {subs:,} | Date: {date} | ==> {status}")
        print()
    
    print(f"=== KET QUA: {ok_count} video dat tieu chi (trong 1 nam + tren 100K views) ===")
