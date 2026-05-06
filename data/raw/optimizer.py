import csv
import os

def load_csv(filename):
    if not os.path.exists(filename):
        print(f"[WARNING] File not found: {filename}")
        return []
    with open(filename, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def build_lookups():
    content = {}
    for row in load_csv('content.csv'):
        content[str(row['content_id'])] = {
            'creator_id':        str(row['creator_id']),
            'content_type':      row['content_type'],
            'created_timestamp': row['created_timestamp'],
            'time_sensitivity':  row['time_sensitivity'].strip().lower(),
        }
    creators = {}
    for row in load_csv('creators.csv'):
        creators[str(row['creator_id'])] = {
            'base_engagement': float(row['base_engagement']),
            'cooldown_hours':  float(row['cooldown_hours']),
        }
    history = {}
    for row in load_csv('historical_engagement.csv'):
        key = (str(row['creator_id']), row['platform'], row['content_type'], str(row['time_slot']))
        history[key] = float(row['avg_engagement'])
    platform_activity = {}
    for row in load_csv('platform_activity.csv'):
        key = (row['platform'], str(row['time_slot']))
        platform_activity[key] = float(row['activity_score'])
    creator_platforms = {}
    for (creator_id, platform, content_type, time_slot) in history:
        if creator_id not in creator_platforms:
            creator_platforms[creator_id] = set()
        creator_platforms[creator_id].add(platform)
    return content, creators, history, platform_activity, creator_platforms

POST_NOW_THRESHOLD = 0.87
DEFAULT_ACTIVITY   = 0.5
DEFAULT_HISTORY    = 0.5

def base_score(creator):
    if creator is None:
        return 0.5
    return min(creator['base_engagement'] / 2.0, 1.0)

def activity_score(platform, time_slot, platform_activity):
    val = platform_activity.get((platform, str(time_slot)))
    return float(val) if val is not None else DEFAULT_ACTIVITY

def history_score(creator_id, platform, content_type, time_slot, history):
    val = history.get((str(creator_id), platform, content_type, str(time_slot)))
    return float(val) if val is not None else DEFAULT_HISTORY

def compute_score(creator_id, platform, content_type, time_slot, creators, history, platform_activity):
    b = base_score(creators.get(str(creator_id)))
    a = activity_score(platform, time_slot, platform_activity)
    h = history_score(creator_id, platform, content_type, time_slot, history)
    return round(b * a * h, 4)

def find_best_slot(creator_id, content_type, creator_platforms, history, platform_activity):
    best_platform, best_slot, best_val = 'Instagram', 12, -1
    for platform in creator_platforms.get(str(creator_id), {'Instagram', 'YouTube'}):
        for hour in range(24):
            val = activity_score(platform, hour, platform_activity) * history_score(creator_id, platform, content_type, hour, history)
            if val > best_val:
                best_val, best_platform, best_slot = val, platform, hour
    return best_platform, best_slot

def decide(content_id, content_row, creators, history, platform_activity, creator_platforms):
    creator_id   = content_row['creator_id']
    content_type = content_row['content_type']
    sensitivity  = content_row['time_sensitivity']
    best_platform, best_slot = find_best_slot(creator_id, content_type, creator_platforms, history, platform_activity)
    score = compute_score(creator_id, best_platform, content_type, best_slot, creators, history, platform_activity)
    if sensitivity == 'high':
        score = min(score * 1.3, 1.0)
    elif sensitivity == 'medium':
        score = min(score * 1.15, 1.0)
    return {
        'content_id': content_id,
        'platform':   best_platform,
        'time_slot':  best_slot,
        'decision':   'post_now' if score >= POST_NOW_THRESHOLD else 'schedule',
        'score':      score,
    }

def run():
    print("Loading CSVs...")
    content, creators, history, platform_activity, creator_platforms = build_lookups()
    if not content:
        print("[ERROR] content.csv is empty or missing.")
        return
    print(f"Loaded: {len(content)} content rows | {len(creators)} creators | {len(history)} history records | {len(platform_activity)} activity slots\n")
    results = []
    for content_id, content_row in content.items():
        results.append(decide(content_id, content_row, creators, history, platform_activity, creator_platforms))
    with open('submission.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['content_id', 'platform', 'time_slot', 'decision'])
        writer.writeheader()
        for r in results:
            writer.writerow({k: r[k] for k in ['content_id', 'platform', 'time_slot', 'decision']})
    post_now = sum(1 for r in results if r['decision'] == 'post_now')
    print(f"Done! submission.csv written with {len(results)} rows.")
    print(f"  POST_NOW : {post_now}")
    print(f"  SCHEDULE : {len(results) - post_now}")

if __name__ == '__main__':
    run()