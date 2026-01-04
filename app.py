import streamlit as st
import pandas as pd
import statistics
import requests
import re
import json
import os
import time
import html
import collections
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="YouTube Intel - V28.1 Pure Max Volume",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

SETTINGS_FILE = "settings.json"
HISTORY_FILE = "history.json"
SEARCH_LOG_FILE = "search_log.json"

# Inisialisasi State
if 'search_results' not in st.session_state:
    st.session_state['search_results'] = None
if 'total_scanned' not in st.session_state:
    st.session_state['total_scanned'] = 0
if 'current_key_index' not in st.session_state:
    st.session_state['current_key_index'] = 0
if 'init_done' not in st.session_state:
    st.session_state['init_done'] = False
if 'seo_results' not in st.session_state:
    st.session_state['seo_results'] = None 
if 'debug_info' not in st.session_state:
    st.session_state['debug_info'] = {}

# ==========================================
# 2. UTILS & DATABASE
# ==========================================
def clean_filename(text):
    text = html.unescape(text)
    cleaned = re.sub(r'[\\/*?:"<>|]', "", text)
    return cleaned.strip()

def load_settings():
    config = {
        "saved_api_keys": "",
        "saved_scan_mode": "⚖️ Sedang",
        "saved_input_jam": 0,
        "saved_input_menit": 58,
        "saved_max_subs": 0, 
        "saved_min_views": 1000,
        "saved_days_back": 30,
        "saved_dark_mode": True
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                saved = json.load(f)
                config.update(saved)
        except:
            pass
    return config

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def load_search_log():
    if os.path.exists(SEARCH_LOG_FILE):
        try:
            with open(SEARCH_LOG_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_search_log(query, mode):
    log = load_search_log()
    display_query = query if query.strip() != "" else "(Tanpa Kata Kunci)"
    new_item = {
        "query": display_query,
        "mode": mode, 
        "time": datetime.now().strftime("%d/%m %H:%M")
    }
    log = [x for x in log if x['query'].lower() != display_query.lower() or x['mode'] != mode]
    log.insert(0, new_item)
    with open(SEARCH_LOG_FILE, "w") as f:
        json.dump(log[:30], f)

def delete_search_log(index=None, delete_all=False):
    if delete_all:
        with open(SEARCH_LOG_FILE, "w") as f:
            json.dump([], f)
    else:
        log = load_search_log()
        if 0 <= index < len(log):
            log.pop(index)
            with open(SEARCH_LOG_FILE, "w") as f:
                json.dump(log, f)

def mark_as_downloaded(video_id, title):
    history = load_history()
    history[video_id] = {
        "title": title,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f)
    except:
        pass

initial_config = load_settings()
download_history = load_history()

if not st.session_state['init_done']:
    modes = ["🌱 Hemat", "⚖️ Sedang", "🔥 Agresif", "☠️ BRUTAL"]
    idx = 1
    if initial_config["saved_scan_mode"] in modes:
        idx = modes.index(initial_config["saved_scan_mode"])
    st.session_state['scan_mode_idx'] = idx
    st.session_state['init_done'] = True

def auto_save():
    current_settings = {
        "saved_api_keys": st.session_state.widget_api_keys,
        "saved_scan_mode": st.session_state.widget_scan_mode,
        "saved_input_jam": st.session_state.widget_jam,
        "saved_input_menit": st.session_state.widget_menit,
        "saved_max_subs": st.session_state.widget_max_subs,
        "saved_min_views": st.session_state.widget_min_views,
        "saved_days_back": st.session_state.widget_days_back,
        "saved_dark_mode": st.session_state.get("widget_dark_mode", True)
    }
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(current_settings, f)
    except:
        pass

# ==========================================
# 3. TAMPILAN & CSS
# ==========================================
with st.sidebar:
    st.header("🎨 Tampilan")
    is_dark_mode = st.toggle(
        "🌙 Mode Gelap", 
        value=initial_config["saved_dark_mode"], 
        key="widget_dark_mode", 
        on_change=auto_save
    )

if is_dark_mode:
    bg_color, sidebar_bg, text_color = "#0E1117", "#262730", "#FAFAFA"
    input_bg, border_color = "#31333F", "#4b5563"
else:
    bg_color, sidebar_bg, text_color = "#FFFFFF", "#F0F2F6", "#000000"
    input_bg, border_color = "#FFFFFF", "#e5e7eb"

st.markdown(f"""
<style>
    .stApp {{ background-color: {bg_color}; color: {text_color}; }}
    [data-testid="stSidebar"] {{ background-color: {sidebar_bg}; border-right: 1px solid {border_color}; }}
    [data-testid="stSidebar"] * {{ color: {text_color} !important; }}
    
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
        background-color: {input_bg} !important; color: {text_color} !important; border: 1px solid {border_color} !important;
    }}
    .stTextInput label, .stNumberInput label, .stTextArea label {{ color: {text_color} !important; font-weight: 600 !important; }}
    button[data-baseweb="tab"] {{ background-color: {sidebar_bg} !important; color: {text_color} !important; }}
    
    .spy-box {{ background-color: #fffbeb; color: #78350f; padding: 20px; border-radius: 8px; border: 1px solid #fcd34d; margin-bottom: 20px; }}
    .spy-title {{ font-size: 1.2em; font-weight: 900; color: #b45309; border-bottom: 2px solid #fcd34d; padding-bottom: 5px; margin-bottom: 10px; text-transform: uppercase; }}
    .spy-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }}
    .spy-item {{ background: #ffffff; padding: 8px; border-radius: 4px; border: 1px solid #e5e7eb; font-size: 0.9em; color: #333; }}
    .spy-label {{ font-weight: bold; color: #555; display: block; font-size: 0.8em; text-transform: uppercase; }}
    .spy-val {{ font-weight: bold; font-size: 1.1em; color: #000; }}
    
    .hist-item {{ font-size: 0.85em; padding: 5px 0; border-bottom: 1px solid {border_color}; }}
    .hist-mode {{ font-size: 0.7em; background: #fcd34d; color: #000; padding: 1px 4px; border-radius: 3px; margin-right: 5px; }}
    
    .key-count {{ font-size: 0.8em; color: #aaa; margin-top: -10px; margin-bottom: 10px; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. FUNGSI LOGIKA (BACKEND)
# ==========================================

def parse_duration(pt_string):
    try:
        pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
        match = pattern.match(pt_string)
        if not match: return 0
        h, m, s = match.groups()
        return (int(h or 0) * 3600) + (int(m or 0) * 60) + int(s or 0)
    except:
        return 0

def format_duration_human(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}j {m}m {s}d" if h > 0 else f"{m}m {s}d"

def get_videos_details_batch(youtube, video_ids):
    if not video_ids: return {}
    results = {}
    try:
        res = youtube.videos().list(part="contentDetails,statistics,snippet", id=','.join(video_ids)).execute()
        for item in res.get('items', []):
            vid = item['id']
            dur_str = item['contentDetails']['duration']
            sec = parse_duration(dur_str)
            results[vid] = {
                "title": html.unescape(item['snippet']['title']),
                "duration_text": format_duration_human(sec),
                "duration_seconds": sec,
                "views": int(item['statistics'].get('viewCount', 0)),
                "url": f"https://www.youtube.com/watch?v={vid}"
            }
    except:
        pass
    return results

def execute_channel_spy(api_key, channel_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    spy_data = {
        "channel_desc": "-", "channel_keywords": [], 
        "channel_age": 0, "channel_created": "-", 
        "subscriber_count": 0, "total_views_all": 0, "total_video_count": 0,
        "live_count": 0, "reguler_count": 0,
        "top_live_list": [], "top_reg_list": [] 
    }
    try:
        ch_res = youtube.channels().list(part="snippet,statistics,brandingSettings", id=channel_id).execute()
        if ch_res['items']:
            item = ch_res['items'][0]
            stt = item['statistics']
            snp = item['snippet']
            brd = item.get('brandingSettings', {}).get('channel', {})
            spy_data["total_views_all"] = int(stt.get('viewCount', 0))
            spy_data["total_video_count"] = int(stt.get('videoCount', 0))
            if not stt.get('hiddenSubscriberCount'):
                spy_data["subscriber_count"] = int(stt.get('subscriberCount', 0))
            spy_data["channel_desc"] = snp.get('description', '-')
            raw_kw = brd.get('keywords', '')
            if raw_kw:
                import shlex
                try: spy_data["channel_keywords"] = shlex.split(raw_kw)
                except: spy_data["channel_keywords"] = raw_kw.split(' ')
            created_at_str = snp.get('publishedAt', '') 
            if created_at_str:
                created_date = datetime.strptime(created_at_str[:10], "%Y-%m-%d")
                now = datetime.now()
                spy_data["channel_age"] = round((now - created_date).days / 365, 1)
                spy_data["channel_created"] = created_date.strftime("%Y-%m-%d")

        live_req = youtube.search().list(part="id", channelId=channel_id, type="video", eventType="completed", order="viewCount", maxResults=3).execute()
        spy_data["live_count"] = live_req.get('pageInfo', {}).get('totalResults', 0)
        live_ids = [i['id']['videoId'] for i in live_req.get('items', [])]

        reg_req = youtube.search().list(part="id", channelId=channel_id, type="video", order="viewCount", maxResults=3).execute()
        spy_data["reguler_count"] = max(0, spy_data["total_video_count"] - spy_data["live_count"])
        reg_ids = [i['id']['videoId'] for i in reg_req.get('items', [])]

        all_ids_to_fetch = live_ids + reg_ids
        details_map = get_videos_details_batch(youtube, all_ids_to_fetch)

        for vid in live_ids:
            if vid in details_map: spy_data["top_live_list"].append(details_map[vid])
        for vid in reg_ids:
            if vid in details_map: spy_data["top_reg_list"].append(details_map[vid])
    except: return None
    return spy_data

@st.cache_data(ttl=600) 
def search_viral_videos_fast(api_keys_list, keyword, max_subs, min_views, days_back, target_limit, min_total_seconds, max_total_seconds):
    # Jika keyword kosong, gunakan pencarian wildcard '*' agar tetap menemukan video populer
    search_query = keyword if keyword.strip() != "" else "*"
    
    published_after = (datetime.now() - timedelta(days=days_back)).isoformat("T") + "Z"
    all_video_items = []
    next_page_token = None
    pages_needed = (target_limit // 50) + (1 if target_limit % 50 > 0 else 0)
    pages_fetched = 0
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    while pages_fetched < pages_needed:
        current_idx = st.session_state['current_key_index']
        if current_idx >= len(api_keys_list): current_idx = 0
        current_key = api_keys_list[current_idx].strip()
        try:
            youtube = build('youtube', 'v3', developerKey=current_key)
            status_text.write(f"🔥 Scanning... {len(all_video_items)}/{target_limit} (Key #{current_idx+1})")
            search_req = youtube.search().list(part="snippet", q=search_query, order="viewCount", publishedAfter=published_after, type="video", maxResults=50, pageToken=next_page_token)
            search_res = search_req.execute()
            items = search_res.get('items', [])
            all_video_items.extend(items)
            next_page_token = search_res.get('nextPageToken')
            pages_fetched += 1
            progress_bar.progress(min(len(all_video_items) / target_limit, 1.0))
            if not next_page_token or len(all_video_items) >= target_limit: break
        except HttpError as e:
            if e.resp.status in [403, 429, 500, 503]:
                new_index = (current_idx + 1) % len(api_keys_list)
                st.session_state['current_key_index'] = new_index
                if new_index == 0 and pages_fetched == 0:
                    st.error("❌ SEMUA API KEY HABIS!")
                    return [], 0
                continue
            else: break
    
    progress_bar.empty()
    status_text.empty()
    if not all_video_items: return [], 0

    active_key = api_keys_list[st.session_state['current_key_index']].strip()
    youtube = build('youtube', 'v3', developerKey=active_key)
    
    channel_ids = list(set([item['snippet']['channelId'] for item in all_video_items]))
    subs_map = {}
    for i in range(0, len(channel_ids), 50):
        chunk = channel_ids[i:i+50]
        try:
            c_res = youtube.channels().list(part="statistics", id=','.join(chunk)).execute()
            for item in c_res.get('items', []):
                val = item['statistics']['hiddenSubscriberCount']
                subs_map[item['id']] = 0 if val else int(item['statistics']['subscriberCount'])
        except: pass

    ids_to_check = [v['id']['videoId'] for v in all_video_items if subs_map.get(v['snippet']['channelId'], 0) < max_subs] if max_subs > 0 else [v['id']['videoId'] for v in all_video_items]
    ids_to_check = ids_to_check[:1000]
    
    final_data = []
    if ids_to_check:
        check_msg = st.empty()
        for i in range(0, len(ids_to_check), 50):
            chunk = ids_to_check[i:i+50]
            check_msg.caption(f"🕵️ Filter Detail Video... {i}/{len(ids_to_check)}")
            try:
                v_res = youtube.videos().list(part="snippet,statistics,contentDetails", id=','.join(chunk)).execute()
                for item in v_res['items']:
                    stats = item['statistics']
                    snippet = item['snippet']
                    content = item['contentDetails']
                    views = int(stats.get('viewCount', 0))
                    duration_sec = parse_duration(content['duration'])
                    
                    # LOGIKA FILTER DURASI (MIN & MAKS)
                    if not (min_total_seconds <= duration_sec <= max_total_seconds): 
                        continue
                        
                    if views < min_views: continue
                    eng_rate = ((int(stats.get('likeCount', 0)) + int(stats.get('commentCount', 0))) / views * 100) if views > 0 else 0
                    tags_list = snippet.get('tags', [])
                    final_data.append({
                        "Thumbnail": snippet['thumbnails']['high']['url'],
                        "Judul Video": html.unescape(snippet['title']),
                        "Channel": html.unescape(snippet['channelTitle']),
                        "ChannelId": snippet['channelId'],
                        "Subs": subs_map.get(snippet['channelId'], 0),
                        "Views": views,
                        "Engagement": round(eng_rate, 2),
                        "Durasi": format_duration_human(duration_sec),
                        "Durasi Detik": duration_sec,
                        "Tags List": tags_list,
                        "Deskripsi": html.unescape(snippet.get('description', "")),
                        "Link": f"https://www.youtube.com/watch?v={item['id']}",
                        "VideoId": item['id']
                    })
            except: pass
        check_msg.empty()
    return final_data, len(all_video_items)

# ==========================================
# 5. NEW: ANALISA SEO VIRAL (PURE STATS & MAX VOLUME)
# ==========================================

def backfill_one_word_keywords(tag_stats, min_freq=3):
    existing_1_word = set()
    for k, v in tag_stats.items():
        if v['len'] == 1:
            existing_1_word.add(k)

    stopwords = {'and', 'the', 'with', 'for', 'you', 'from', 'in', 'on', 'at', 'to', 'of', 'by', 'my', 'is', 'a', 'it', 'video', 'videos', 'lyric', 'lyrics', 'official', 'hd', '4k', 'mv'}

    new_entries = {}

    for k, v in tag_stats.items():
        # Only process if parent meets frequency criteria
        if (v['len'] == 2 or v['len'] == 3) and v['count'] >= min_freq: 
            words = k.split()
            for w in words:
                w_clean = w.strip()
                if len(w_clean) > 2 and w_clean not in stopwords and w_clean not in existing_1_word:
                    if w_clean in new_entries:
                        avg_v_new = v['total_views'] // v['count']
                        avg_v_old = new_entries[w_clean]['total_views'] // new_entries[w_clean]['count']
                        if avg_v_new > avg_v_old:
                            new_entries[w_clean] = {
                                'count': v['count'], 
                                'total_views': v['total_views'], 
                                'total_likes': v['total_likes'], 
                                'len': 1 
                            }
                    else:
                        new_entries[w_clean] = {
                            'count': v['count'], 
                            'total_views': v['total_views'], 
                            'total_likes': v['total_likes'], 
                            'len': 1
                        }
                    
    final_stats = tag_stats.copy()
    final_stats.update(new_entries)
    return final_stats

def analyze_viral_seo(api_keys_list, title_query, days_back, max_subs, min_views, min_duration_sec, mode_research, length_filters):
    
    # FRESH STATS
    debug_stats = {
        'total_found_search': 0,
        'blocked_duration': 0,
        'blocked_views': 0,
        'blocked_subs': 0,
        'passed_final': 0,
        'auto_rescued': False,
        'unique_channels_count': 0,
        'total_videos_processed': 0,
        'real_total_views': 0,
        'yt_key_line': 0
    }
    
    tag_stats = {} 

    target_counts = []
    if "1 Kata" in length_filters: target_counts.append(1)
    if "2 Kata" in length_filters: target_counts.append(2)
    if "3+ Kata" in length_filters: target_counts.append(3)
    if not target_counts: target_counts = [1, 2, 3]

    # --- BOOSTED FETCH COUNT FOR "LOW RESULT" FIX ---
    if mode_research == "🌱 Hemat":
        target_fetch_count = 200 # Up from 100
    elif mode_research == "⚖️ Sedang":
        target_fetch_count = 500 # Up from 250
    elif mode_research == "🔥 Agresif":
        target_fetch_count = 1000 # Up from 450
    else: # BRUTAL / GOD MODE
        target_fetch_count = 1500 # Massive

    published_after = (datetime.now() - timedelta(days=days_back)).isoformat("T") + "Z"
    
    idx = st.session_state['current_key_index']
    if idx >= len(api_keys_list): idx = 0
    
    # KEY ROTATION LOGIC
    raw_items = []
    video_ids = []
    next_page_token = None
    
    while len(raw_items) < target_fetch_count:
        if idx >= len(api_keys_list): idx = 0
        active_key = api_keys_list[idx].strip()
        youtube = build('youtube', 'v3', developerKey=active_key)
        
        try:
            search_req = youtube.search().list(
                part="id,snippet", 
                q=title_query, 
                order="viewCount", 
                publishedAfter=published_after, 
                type="video", 
                maxResults=50, 
                pageToken=next_page_token
            )
            search_res = search_req.execute()
            items = search_res.get('items', [])
            
            if not items: break
            
            raw_items.extend(items)
            next_page_token = search_res.get('nextPageToken')
            
            if not next_page_token: break
            
        except HttpError as e:
            if e.resp.status in [403, 429]:
                idx = (idx + 1) % len(api_keys_list)
                st.session_state['current_key_index'] = idx
                continue
            else:
                break 
    
    video_ids = [item['id']['videoId'] for item in raw_items]
    debug_stats['total_found_search'] = len(video_ids)
    debug_stats['yt_key_line'] = idx + 1 

    if not video_ids: 
        return [], debug_stats

    # DETAILS FETCHING (ROTATION AWARE)
    valid_items_stage1 = []
    channel_ids_to_check = []
    
    for i in range(0, len(video_ids), 50):
        chunk_ids = video_ids[i:i+50]
        max_retries = len(api_keys_list)
        attempts = 0
        success = False
        
        while attempts < max_retries and not success:
            if idx >= len(api_keys_list): idx = 0
            active_key = api_keys_list[idx].strip()
            youtube = build('youtube', 'v3', developerKey=active_key)
            
            try:
                vid_res = youtube.videos().list(
                    part="snippet,statistics,contentDetails", id=','.join(chunk_ids)
                ).execute()
                
                for item in vid_res.get('items', []):
                    stats = item['statistics']
                    content = item['contentDetails']
                    views = int(stats.get('viewCount', 0))
                    dur_sec = parse_duration(content['duration'])
                    
                    if dur_sec < min_duration_sec: 
                        debug_stats['blocked_duration'] += 1
                        continue
                    if views < min_views: 
                        debug_stats['blocked_views'] += 1
                        continue
                    
                    valid_items_stage1.append(item)
                    channel_ids_to_check.append(item['snippet']['channelId'])
                success = True
            except HttpError as e:
                if e.resp.status in [403, 429]:
                    idx = (idx + 1) % len(api_keys_list)
                    st.session_state['current_key_index'] = idx
                    attempts += 1
                else:
                    break

    if not valid_items_stage1: return [], debug_stats
    
    # CHANNEL FETCHING (ROTATION AWARE)
    subs_map = {}
    unique_chans = list(set(channel_ids_to_check))
    
    for i in range(0, len(unique_chans), 50):
        chunk = unique_chans[i:i+50]
        max_retries = len(api_keys_list)
        attempts = 0
        success = False
        
        while attempts < max_retries and not success:
            if idx >= len(api_keys_list): idx = 0
            active_key = api_keys_list[idx].strip()
            youtube = build('youtube', 'v3', developerKey=active_key)
            
            try:
                c_res = youtube.channels().list(part="statistics", id=','.join(chunk)).execute()
                for c_item in c_res.get('items', []):
                    if c_item['statistics'].get('hiddenSubscriberCount'):
                        subs_map[c_item['id']] = 0
                    else:
                        subs_map[c_item['id']] = int(c_item['statistics'].get('subscriberCount', 0))
                success = True
            except HttpError as e:
                if e.resp.status in [403, 429]:
                    idx = (idx + 1) % len(api_keys_list)
                    st.session_state['current_key_index'] = idx
                    attempts += 1
                else:
                    break

    items_to_process = []
    items_rescued_from_subs = [] 

    for item in valid_items_stage1:
        cid = item['snippet']['channelId']
        subs = subs_map.get(cid, 0) 
        
        if max_subs > 0:
            if subs > max_subs:
                debug_stats['blocked_subs'] += 1
                items_rescued_from_subs.append(item) 
                continue
        
        debug_stats['passed_final'] += 1
        items_to_process.append(item)

    if len(items_to_process) == 0 and len(items_rescued_from_subs) > 0:
        items_to_process = items_rescued_from_subs
        debug_stats['auto_rescued'] = True 
        debug_stats['passed_final'] = len(items_rescued_from_subs)

    unique_channels_final = set()
    real_total_views_accumulated = 0 

    for item in items_to_process:
        unique_channels_final.add(item['snippet']['channelId'])
        real_total_views_accumulated += int(item['statistics'].get('viewCount', 0))

    debug_stats['unique_channels_count'] = len(unique_channels_final)
    debug_stats['total_videos_processed'] = len(items_to_process)
    debug_stats['real_total_views'] = real_total_views_accumulated 

    for item in items_to_process:
        views = int(item['statistics'].get('viewCount', 0))
        likes = int(item['statistics'].get('likeCount', 0))
        tags = item['snippet'].get('tags', [])
        title_words = re.findall(r'\w+', item['snippet']['title'].lower())
        
        all_keywords = tags + [w for w in title_words if len(w) > 3]
        
        for tag in all_keywords:
            tag_clean = tag.lower().strip()
            
            technical_junk = ['hd', '4k', '1080p', 'hq', 'official video', 'lyric video', 'official audio']
            if any(junk in tag_clean for junk in technical_junk): continue

            word_len = len(tag_clean.split())
            
            is_valid_len = False
            if word_len == 1 and 1 in target_counts: is_valid_len = True
            elif word_len == 2 and 2 in target_counts: is_valid_len = True
            elif word_len >= 3 and 3 in target_counts: is_valid_len = True
            
            if not is_valid_len: continue

            if tag_clean not in tag_stats:
                tag_stats[tag_clean] = {'count': 0, 'total_views': 0, 'total_likes': 0, 'len': word_len}
            
            tag_stats[tag_clean]['count'] += 1
            tag_stats[tag_clean]['total_views'] += views
            tag_stats[tag_clean]['total_likes'] += likes

    # === 1. FILTER FREKUENSI (MIN 3 VIDEO) ===
    tag_stats = {k: v for k, v in tag_stats.items() if v['count'] >= 3}

    # === 2. BACKFILL ===
    tag_stats = backfill_one_word_keywords(tag_stats, min_freq=3)

    results = []
    # Stopwords minimal
    stopwords = ['and', 'the', 'with', 'for', 'you', 'from', 'in', 'on', 'at', 'to', 'of', 'by', 'my', 'is', 'a', 'it', 'video', 'videos', 'lyric', 'lyrics', 'official', 'hd', '4k']
    
    for tag, data in tag_stats.items():
        if tag in stopwords: continue
        
        freq = data['count']
        avg_views = data['total_views'] / freq
        avg_likes = data['total_likes'] / freq
        
        score_view = min((avg_views / 50000) * 40, 40)
        score_freq = min(freq * 10, 30)
        score_eng = min((avg_likes / (avg_views+1) * 100) * 10, 30)
        final_score = score_view + score_freq + score_eng
        
        cat_text = "1 Kata"
        if data['len'] == 2: cat_text = "2 Kata"
        elif data['len'] >= 3: cat_text = "3+ Kata"

        results.append({
            "Jenis": cat_text,
            "Kata Kunci": tag,
            "Muncul di Video": freq,
            "Rata-rata Views": int(avg_views),
            "Engagement Score": round(score_eng, 1),
            "Skor Viral": round(final_score, 1),
            "word_count_raw": data['len']
        })
        
    return results, debug_stats

# ==========================================
# 6. SIDEBAR
# ==========================================
with st.sidebar:
    st.header("🎛️ Panel Kontrol")
    with st.expander("🔑 Kunci Akses (Multi-Key)", expanded=True):
        api_keys_raw = st.text_area("YouTube API Keys:", value=initial_config["saved_api_keys"], height=80, key="widget_api_keys", on_change=auto_save)
        api_keys_list = [k.strip() for k in api_keys_raw.split('\n') if k.strip()]
        
        if api_keys_list: st.markdown(f'<div class="key-status status-ok">✅ {len(api_keys_list)} YT Key Ready.</div>', unsafe_allow_html=True)
        else: st.warning("⚠️ Masukkan YT Key dulu.")

    with st.expander("🚀 Mode Scan", expanded=True):
        scan_mode = st.radio("Kekuatan:", ("🌱 Hemat", "⚖️ Sedang", "🔥 Agresif", "☠️ BRUTAL"), index=st.session_state['scan_mode_idx'], key="widget_scan_mode", on_change=auto_save)
        if "Hemat" in scan_mode: target_limit = 50
        elif "Sedang" in scan_mode: target_limit = 150
        elif "Agresif" in scan_mode: target_limit = 500
        else:
            target_limit = 2000
            st.markdown('<div class="brutal-warning">⚠️ AWAS: Boros Kuota!</div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("⏳ Filter Durasi (Range)")
    
    st.markdown("**Batas Minimal:**")
    c1, c2 = st.columns(2)
    with c1: input_jam = st.number_input("Jam", 0, 24, initial_config["saved_input_jam"], key="widget_jam", on_change=auto_save)
    with c2: input_menit = st.number_input("Menit", 0, 59, initial_config["saved_input_menit"], key="widget_menit", on_change=auto_save)
    min_total_seconds = (input_jam * 3600) + (input_menit * 60)

    # FITUR BARU: Filter Maksimal
    st.markdown("**Batas Maksimal:**")
    use_max_duration = st.toggle("Aktifkan Batas Maksimal", value=False)
    max_total_seconds = 999999 
    if use_max_duration:
        c3, c4 = st.columns(2)
        with c3: max_jam = st.number_input("Maks Jam", 0, 24, 0)
        with c4: max_menit = st.number_input("Maks Menit", 0, 59, 1)
        max_total_seconds = (max_jam * 3600) + (max_menit * 60)
    
    st.divider()
    with st.expander("⚙️ Filter Lanjutan"):
        st.caption("ℹ️ Set '0' pada Max Subs untuk mematikan filter Subs.")
        max_subs = st.number_input("Maks. Subs", 0, value=initial_config["saved_max_subs"], step=10000, key="widget_max_subs", on_change=auto_save)
        min_views = st.number_input("Min. Views", 0, value=initial_config["saved_min_views"], step=500, key="widget_min_views", on_change=auto_save)
        days_back = st.slider("Umur Video", 1, 30, initial_config["saved_days_back"], key="widget_days_back", on_change=auto_save)

    st.divider()
    with st.expander("🕒 Riwayat Pencarian", expanded=True):
        if st.button("🗑️ Hapus Semua History", use_container_width=True):
            delete_search_log(delete_all=True)
            st.rerun()
            
        logs = load_search_log()
        if logs:
            for i, item in enumerate(logs):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"<div class='hist-item'><span class='hist-mode'>{item['mode']}</span>{item['query']}</div>", unsafe_allow_html=True)
                with c2:
                    if st.button("❌", key=f"del_h_{i}"):
                        delete_search_log(index=i)
                        st.rerun()
        else:
            st.caption("Belum ada riwayat.")

# ==========================================
# 7. HALAMAN UTAMA
# ==========================================
st.title("💎 YouTube Intel: V28.1 Pure Max Volume")

if not api_keys_list:
    st.warning("👈 Masukkan API Key di sidebar.")
    st.stop()

tab1, tab2 = st.tabs(["🕵️  Cari & Spy Metadata", "⚖️  Analisa Keyword Viral"])

with tab1:
    c1, c2 = st.columns([3, 1])
    with c1: keyword_vid = st.text_input("Topik Video:", placeholder="Kosongkan untuk scan global berdasarkan filter...")
    with c2: 
        st.write("")
        st.write("")
        if st.button("🔎 Scan Data", type="primary", use_container_width=True):
            save_search_log(keyword_vid, "Metadata")
            
            for key in list(st.session_state.keys()):
                if key.startswith("spy_data_") or key.startswith("meta_"): del st.session_state[key]
            
            data, total = search_viral_videos_fast(
                api_keys_list, 
                keyword_vid, 
                max_subs, 
                min_views, 
                days_back, 
                target_limit, 
                min_total_seconds,
                max_total_seconds
            )
            st.session_state['search_results'] = data
            st.session_state['total_scanned'] = total
            download_history = load_history()

    if st.session_state['search_results'] is not None:
        data = st.session_state['search_results']
        total = st.session_state['total_scanned']
        if data:
            df = pd.DataFrame(data).sort_values(by='Durasi Detik', ascending=False)
            st.success(f"✅ Ditemukan {len(df)} video potensial (Sample: {total}).")
            st.dataframe(df[['Judul Video', 'Views', 'Durasi', 'Engagement', 'Subs']], use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("📝 Metadata Editor & Spy Report")

            for idx, row in df.iterrows():
                k_title, k_chan, k_link = f"meta_title_{idx}", f"meta_chan_{idx}", f"meta_link_{idx}"
                k_tags, k_desc, k_spy = f"meta_tags_{idx}", f"meta_desc_{idx}", f"spy_data_{idx}"

                if k_title not in st.session_state: st.session_state[k_title] = row['Judul Video']
                if k_chan not in st.session_state: st.session_state[k_chan] = row['Channel']
                if k_link not in st.session_state: st.session_state[k_link] = row['Link']
                if k_tags not in st.session_state: st.session_state[k_tags] = ", ".join(row['Tags List'])
                if k_desc not in st.session_state: st.session_state[k_desc] = row['Deskripsi']

                vid_id = row['VideoId']
                is_downloaded = vid_id in download_history
                
                header_text = f"📂 {row['Judul Video']} | ⏱️ {row['Durasi']}"
                if is_downloaded: header_text += " ✅ SUDAH PERNAH DIDOWNLOAD"

                with st.expander(header_text, expanded=False):
                    if is_downloaded:
                        st.info(f"📌 Downloaded: {download_history[vid_id]['date']}")

                    spy_placeholder = st.empty()
                    spy_txt_formatted = "Data Spy belum diambil."
                    json_data_export = {}

                    if k_spy in st.session_state:
                        spy = st.session_state[k_spy]
                        if spy:
                            live_list_ui = "".join([f"<li class='spy-item'><b>{i['title']}</b> ({i['duration_text']}) - 👁️ {i['views']:,}</li>" for i in spy['top_live_list']])
                            reg_list_ui = "".join([f"<li class='spy-item'><b>{i['title']}</b> ({i['duration_text']}) - 👁️ {i['views']:,}</li>" for i in spy['top_reg_list']])
                            
                            spy_placeholder.markdown(f"""
                            <div class="spy-box">
                                <div class="spy-header">🕵️ CHANNEL INTEL: {st.session_state[k_chan]}</div>
                                <div class="spy-grid">
                                    <div class="spy-metric"><span class="sm-label">Umur</span><span class="sm-val">{spy['channel_age']} Thn</span></div>
                                    <div class="spy-metric"><span class="sm-label">Subs</span><span class="sm-val">{spy['subscriber_count']:,}</span></div>
                                    <div class="spy-metric"><span class="sm-label">Total Views</span><span class="sm-val">{spy['total_views_all']:,}</span></div>
                                    <div class="spy-metric"><span class="sm-label">Total Vid</span><span class="sm-val">{spy['total_video_count']:,}</span></div>
                                    <div class="spy-metric"><span class="sm-label">Live</span><span class="sm-val">{spy['live_count']}</span></div>
                                    <div class="spy-metric"><span class="sm-label">Reguler</span><span class="sm-val">{spy['reguler_count']}</span></div>
                                </div>
                                <div class="spy-section-title">🗝️ KEYWORDS CHANNEL:</div>
                                <div style="font-size:0.9em; font-style:italic;">{spy['channel_keywords']}</div>
                                <div class="spy-section-title">📄 DESKRIPSI CHANNEL:</div>
                                <div class="spy-desc-box">{spy['channel_desc']}</div>
                                <div class="spy-section-title">🔴 TOP 3 LIVE STREAM:</div>
                                <ul class="spy-list">{live_list_ui}</ul>
                                <div class="spy-section-title">📺 TOP 3 VIDEO REGULER:</div>
                                <ul class="spy-list">{reg_list_ui}</ul>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            live_txt_list = [f"{i['title']} ({i['duration_text']} - {i['views']:,} views)" for i in spy['top_live_list']]
                            reg_txt_list = [f"{i['title']} ({i['duration_text']} - {i['views']:,} views)" for i in spy['top_reg_list']]
                            
                            spy_txt_formatted = f"""
CHANNEL_METADATA_START
CHANNEL_NAME: {st.session_state[k_chan]}
CHANNEL_AGE_YEARS: {spy['channel_age']}
CHANNEL_CREATED_DATE: {spy['channel_created']}
TOTAL_SUBSCRIBERS: {spy['subscriber_count']}
TOTAL_VIEWS_GLOBAL: {spy['total_views_all']}
TOTAL_VIDEO_GLOBAL: {spy['total_video_count']}
CHANNEL_METADATA_END

CHANNEL_DETAILS_START
CHANNEL_KEYWORDS:
{spy['channel_keywords']}

CHANNEL_DESCRIPTION:
{spy['channel_desc']}
CHANNEL_DETAILS_END

SPLIT_STATS_START
TOTAL_VIDEO_LIVE: {spy['live_count']}
TOTAL_VIDEO_REGULER: {spy['reguler_count']}
SPLIT_STATS_END

CONTENT_PERFORMANCE_START
TOP_3_LIVE_LIST:
{json.dumps(live_txt_list, indent=2, ensure_ascii=False)}

TOP_3_REGULER_LIST:
{json.dumps(reg_txt_list, indent=2, ensure_ascii=False)}
CONTENT_PERFORMANCE_END
"""
                            tags_list_final = [t.strip() for t in st.session_state[k_tags].split(',')]
                            json_data_export = {
                                "video_metadata": {
                                    "title": st.session_state[k_title],
                                    "channel_name": st.session_state[k_chan],
                                    "url": st.session_state[k_link],
                                    "keywords_konten": tags_list_final,
                                    "description_konten": st.session_state[k_desc]
                                },
                                "channel_intel": spy
                            }
                        else:
                            spy_placeholder.error("Gagal Spy.")
                    else:
                        if spy_placeholder.button("🕵️ Analisa Channel Ini", key=f"btn_spy_{idx}"):
                            with st.spinner("Mengintip data..."):
                                key_idx = st.session_state['current_key_index']
                                key_to_use = api_keys_list[key_idx].strip()
                                spy_result = execute_channel_spy(key_to_use, row['ChannelId'])
                                st.session_state[k_spy] = spy_result
                                st.rerun()

                    col_img, col_data = st.columns([1, 2])
                    with col_img:
                        st.image(row['Thumbnail'], use_container_width=True)
                        st.link_button("▶️ Tonton di YouTube", row['Link'], use_container_width=True)
                        st.write("")
                        
                        safe_chan = clean_filename(st.session_state[k_chan])
                        safe_title = clean_filename(st.session_state[k_title])
                        fname_base = f"{safe_chan} - {safe_title}"[:100]

                        txt_final = f"JUDUL KONTEN:\n{st.session_state[k_title]}\n\nNAMA CHANNEL:\n{st.session_state[k_chan]}\n\nLINK VIDEO:\n{st.session_state[k_link]}\n\nKEYWORDS KONTEN:\n{st.session_state[k_tags]}\n\nDESKRIPSI KONTEN:\n{st.session_state[k_desc]}\n\n{spy_txt_formatted}"
                        
                        st.download_button("📥 Download .TXT (Human)", txt_final, f"{fname_base}.txt", "text/plain", use_container_width=True, key=f"dl_txt_{idx}", on_click=mark_as_downloaded, args=(vid_id, row['Judul Video']))

                        if json_data_export:
                            json_str = json.dumps(json_data_export, indent=4, ensure_ascii=False)
                            st.download_button("🤖 Download .JSON (AI)", json_str, f"{fname_base}.json", "application/json", use_container_width=True, key=f"dl_json_{idx}")
                    
                    with col_data:
                        st.text_input("📌 Judul:", key=k_title)
                        c_a, c_b = st.columns(2)
                        with c_a: st.text_input("👤 Nama Channel:", key=k_chan)
                        with c_b: st.text_input("🔗 Link Video:", key=k_link)
                        st.text_area("🏷️ KEYWORDS KONTEN:", height=100, key=k_tags)
                        st.text_area("📄 DESKRIPSI KONTEN:", height=200, key=k_desc)
        else:
            st.error("Hasil 0. Coba ubah filter.")

# ==========================================
# TAB 2: ANALISA SEO VIRAL (PURE STATS)
# ==========================================
with tab2:
    st.header("⚖️ Analisa Keyword Viral")
    st.markdown("""
    Fitur ini mencari kata kunci dari video viral dengan **Filter Sidebar**.
    Kata kunci hanya akan muncul jika digunakan oleh minimal **3 Video Berbeda** (Validitas Tinggi).
    """)
    
    col_input, col_act = st.columns([3, 1])
    with col_input:
        seo_query = st.text_input("Masukkan Judul Video Kamu:", placeholder="Contoh: Cara Menghasilkan Uang Dari Internet")
        
        c_len, c_ai = st.columns([2, 1])
        with c_len:
            selected_lengths = st.multiselect(
                "Pilih Panjang Kata Kunci:",
                ["1 Kata", "2 Kata", "3+ Kata"],
                default=["1 Kata", "2 Kata"]
            )
        with c_ai:
            st.write("") 
    
    with col_act:
        st.write("")
        st.write("")
        st.write("") 
        if st.button("🚀 Analisa & Filter", type="primary", use_container_width=True):
            if seo_query and selected_lengths:
                
                # --- STATE WIPER ---
                if 'seo_results' in st.session_state: del st.session_state['seo_results']
                if 'debug_info' in st.session_state: del st.session_state['debug_info']
                st.session_state['seo_results'] = None
                
                status_text = f"🔍 Sedang menganalisa topik: '{seo_query}'..."
                with st.spinner(status_text):
                    save_search_log(seo_query, "Viral")

                    mode_now = "Hemat" if "Hemat" in st.session_state.widget_scan_mode else "Maksimal"
                    days_now = st.session_state.widget_days_back
                    max_s = st.session_state.widget_max_subs
                    min_v = st.session_state.widget_min_views
                    min_sec = (st.session_state.widget_jam * 3600) + (st.session_state.widget_menit * 60)
                    
                    res_seo, debug_info = analyze_viral_seo(api_keys_list, seo_query, days_now, max_s, min_v, min_sec, mode_now, selected_lengths)
                    
                    st.session_state['seo_results'] = res_seo
                    st.session_state['debug_info'] = debug_info
            elif not selected_lengths:
                st.warning("Pilih minimal satu jenis panjang kata kunci.")
            else:
                st.warning("Isi judul dulu.")

    if st.session_state['seo_results'] is not None:
        results = st.session_state['seo_results']
        d_info = st.session_state['debug_info']
        
        if len(results) > 0:
            df_seo = pd.DataFrame(results).sort_values(by="Skor Viral", ascending=False).reset_index(drop=True)
            
            best_kw = df_seo.iloc[0]['Kata Kunci']
            avg_comp_views = int(df_seo['Rata-rata Views'].mean())
            total_reach = d_info.get('real_total_views', 0)
            
            if d_info.get('auto_rescued'):
                st.warning("⚠️ **INFO:** Filter 'Max Subs' terlalu ketat. Sistem otomatis mengabaikannya agar hasil tetap muncul.")
            
            # Indikator API Key yang digunakan
            st.caption(f"ℹ️ Menggunakan API: YouTube (Baris {d_info.get('yt_key_line', 1)})")

            # METRICS
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Kata Kunci Raja", best_kw.upper())
            m2.metric("🔥 Total Jangkauan Views", f"{total_reach:,}")
            m3.metric("Rata-rata Views", f"{avg_comp_views:,}")
            m4.metric("Video / Channel", f"{d_info.get('total_videos_processed', 0)} / {d_info.get('unique_channels_count', 0)}")
            
            st.info("💡 **Info:** 'Total Jangkauan Views' adalah jumlah penonton dari semua video yang ditemukan. Angka ini akan NAIK jika kamu menurunkan filter (karena lebih banyak video yang masuk). Rata-rata Views mungkin turun, tapi Total Reach naik.")

            st.divider()

            display_order = ["1 Kata", "2 Kata", "3+ Kata"]
            
            for category in display_order:
                if category in selected_lengths:
                    df_subset = df_seo[df_seo['Jenis'] == category]
                    if not df_subset.empty:
                        st.subheader(f"📂 Tabel Kata Kunci: {category}")
                        st.dataframe(df_subset[['Kata Kunci', 'Muncul di Video', 'Rata-rata Views', 'Skor Viral']], use_container_width=True)
                    else:
                        st.info(f"⚠️ Kategori '{category}': Tidak ditemukan data yang cocok.")
            
            st.divider()
            
            df_csv = df_seo.sort_values(by=['word_count_raw', 'Skor Viral'], ascending=[True, False])
            
            csv_final = df_csv[['Jenis', 'Kata Kunci', 'Skor Viral', 'Rata-rata Views', 'Muncul di Video', 'Engagement Score']]
            csv_data = csv_final.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="📥 Download Tabel Lengkap (.CSV)",
                data=csv_data,
                file_name=f"analisa_viral_{clean_filename(seo_query)}.csv",
                mime="text/csv"
            )
        
        else:
            st.error("❌ Hasil 0 Video.")
            st.markdown(f"""
            **Diagnosa:**
            - Ditemukan: {d_info.get('total_found_search',0)} video awal.
            - Blokir Durasi: {d_info.get('blocked_duration',0)}
            - Blokir Views: {d_info.get('blocked_views',0)}
            - Blokir Subs: {d_info.get('blocked_subs',0)}
            
            **Saran:** Coba ubah 'Umur Video' menjadi lebih lama (Misal 30 Hari) atau ganti Judul.
            """)
