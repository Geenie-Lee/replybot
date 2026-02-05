import re

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
    # [ \t\xa0]는 일반 공백, 탭, 그리고 특수 공백(&nbsp;)을 모두 포함합니다.
    text = re.sub(r"(입금일\s*:\s*)[^\n]+", r"\1★", text)

    return text

# 테스트 실행
sample_text = """
- 결제 금액 : 125,000 원
- 이용 수수료: 71,660 원( 2025-04-14~2025-10-02 /172일)
- 결제대행 수수료 : 8,000 원
- 환불 가능 금액 : 45,340 원  
2. 입금일 :  10/29(수)
"""

print(normalize_refund_template(sample_text))