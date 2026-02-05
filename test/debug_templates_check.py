import json
import collections

try:
    with open('model/reply_templates_80.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Total items in list: {len(data)}")
    
    ids = [item.get('id') for item in data]
    print(f"Total IDs found: {len(ids)}")
    
    # Check for duplicates
    dupes = [item for item, count in collections.Counter(ids).items() if count > 1]
    if dupes:
        print(f"Duplicate IDs found: {dupes}")
        print(f"Count of duplicates: {len(dupes)}")
        
    unique_ids = set(ids)
    print(f"Unique IDs: {len(unique_ids)}")
    
except Exception as e:
    print(e)
