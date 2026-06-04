import urllib.parse
import re
import json
import requests
import sys

def scrape_youtube_search_http(query: str, max_results: int = 5) -> list[dict]:
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Failed to fetch search page: status {response.status_code}")
            return []
            
        html = response.text
        json_match = re.search(r'var ytInitialData\s*=\s*({.*?});', html)
        if not json_match:
            json_match = re.search(r'window\["ytInitialData"\]\s*=\s*({.*?});', html)
            
        if not json_match:
            print("Could not find ytInitialData in page source")
            # Write html to debug
            with open("yt_debug.html", "w", encoding="utf-8") as f:
                f.write(html[:50000])
            return []
            
        data = json.loads(json_match.group(1))
        
        videos = []
        try:
            section_contents = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents']
            for section in section_contents:
                if 'itemSectionRenderer' in section:
                    items = section['itemSectionRenderer']['contents']
                    for item in items:
                        if 'videoRenderer' in item:
                            vr = item['videoRenderer']
                            
                            video_id = vr.get('videoId')
                            if not video_id:
                                continue
                                
                            title = ""
                            try:
                                title = vr['title']['runs'][0]['text']
                            except Exception:
                                pass
                                
                            channel = ""
                            try:
                                channel = vr['ownerText']['runs'][0]['text']
                            except Exception:
                                pass
                                
                            description = ""
                            try:
                                description = "".join([run.get('text', '') for run in vr['descriptionSnippet']['runs']])
                            except Exception:
                                pass
                                
                            views_text = ""
                            view_count = 0
                            try:
                                views_text = vr['viewCountText']['simpleText']
                                match = re.search(r'([\d,]+)\s*views?', views_text.lower())
                                if match:
                                    view_count = int(match.group(1).replace(",", ""))
                            except Exception:
                                try:
                                    views_text = vr['shortViewCountText']['simpleText']
                                except Exception:
                                    pass
                            
                            videos.append({
                                "id": video_id,
                                "url": f"https://www.youtube.com/watch?v={video_id}",
                                "title": title,
                                "channel": channel,
                                "description": description,
                                "views_text": views_text,
                                "view_count": view_count
                            })
                            
                            if len(videos) >= max_results:
                                return videos
        except Exception as err:
            print(f"Error traversing JSON: {err}")
            
        return videos
    except Exception as e:
        print(f"Search failed: {e}")
        return []

if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    
    query = "kubernetes tutorial"
    print(f"Searching YouTube for '{query}' browserlessly via requests...")
    results = scrape_youtube_search_http(query, max_results=3)
    
    print(f"Found {len(results)} videos:")
    for idx, r in enumerate(results):
        print(f"  {idx+1}. Title: {r.get('title')}")
        print(f"     URL: {r.get('url')}")
        print(f"     Channel: {r.get('channel')}")
        print(f"     Views: {r.get('view_count')}")
        print(f"     ID: {r.get('id')}")
