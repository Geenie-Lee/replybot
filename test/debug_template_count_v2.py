import json
import os

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
files = ['model/templates.json', 'model/reply_templates_57.json', 'model/reply_templates_78.json', 'model/reply_templates_80.json']

for fname in files:
    fpath = os.path.join(parent_dir, fname)
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"{fname}: {len(data)}")
    except Exception as e:
        print(f"{fname}: Error {e}")
