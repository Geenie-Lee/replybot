import json
import os
import tomllib

TEMPLATES_FILE = "model/reply_templates_80.json"

# Mock Config Load
if os.path.exists('config/config.toml'):
    with open('config/config.toml', 'rb') as f:
        toml_config = tomllib.load(f)
        if toml_config and 'files' in toml_config:
            if 'templates' in toml_config['files']:
                TEMPLATES_FILE = toml_config['files']['templates']

print(f"Loading: {TEMPLATES_FILE}")

templates_by_id = {}
try:
    with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
        templates_data = json.load(f)
    
    print(f"Items in JSON: {len(templates_data)}")
    
    count = 0
    for template in templates_data:
        template_id = template.get('id')
        if template_id is not None:
            templates_by_id[template_id] = template
            count += 1
            
    print(f"Loaded Dictionary Size: {len(templates_by_id)}")

except Exception as e:
    print(e)
