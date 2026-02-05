import json
import re
import os

TEMPLATES_FILE = "c:/workspace/db/replybot/model/wavve_reply_templates_132.json"

def normalize_refund_template(text):
    if text is None:
        return ""
    
    # 1. 일반 항목 금액 치환 (결제 금액, 결제대행 수수료, 환불 가능 금액)
    text = re.sub(r"(결제 금액\s*:\s*)[\d,]+\s*원", r"\1★", text)
    text = re.sub(r"(결제대행 수수료\s*:\s*)[\d,]+\s*원", r"\1★", text)
    text = re.sub(r"(환불 가능 금액\s*:\s*)[\d,]+\s*원", r"\1★", text)
    
    # 2. 이용 수수료 항목 정밀 치환 (요청하신 형식 반영)
    # 패턴: 이용 수수료: ★ (기간 / 일수)
    usage_fee_pattern = r"이용 수수료\s*:\s*[\d,]+\s*원\s*\(\s*\d{4}-\d{2}-\d{2}~\d{4}-\d{2}-\d{2}\s*/\s*\d+일\)"
    text = re.sub(usage_fee_pattern, "이용 수수료: ★ (기간 / 일수)", text)
    
    # 3. 입금일 치환 (콜론 뒤 공백 유지 후 ★ 밀착)
    text = re.sub(r"(입금일\s*:\s*)[^\n]+", r"\1★", text)

    return text

def main():
    if not os.path.exists(TEMPLATES_FILE):
        print(f"Error: {TEMPLATES_FILE} not found.")
        return

    try:
        with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        updated_count = 0
        
        for item in data:
            original_text = item.get('general_template', '')
            if original_text:
                new_text = normalize_refund_template(original_text)
                if new_text != original_text:
                    item['general_template'] = new_text
                    updated_count += 1
        
        if updated_count > 0:
            with open(TEMPLATES_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Successfully updated {updated_count} templates.")
        else:
            print("No templates needed to be updated.")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
