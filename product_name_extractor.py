import json
import pandas as pd
import re
from typing import Dict, List, Any, Optional

class ProductNameExtractor:
    """상품명 추출 및 치환 시스템"""
    
    def __init__(self, ubase_file: str = "model/enhanced_ubase_agent_unified.json"):
        self.ubase_file = ubase_file
        self.ubase_data = []
        self.customer_index = {}
        self.load_ubase_data()
    
    def load_ubase_data(self):
        """Ubase 데이터 로드"""
        try:
            with open(self.ubase_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            # 데이터 구조 확인 및 처리
            if isinstance(raw_data, dict) and 'data' in raw_data:
                # enhanced_ubase_agent_unified.json 구조
                self.ubase_data = raw_data['data']
                print(f"[INFO] Ubase 메타데이터: {raw_data.get('metadata', {}).get('total_records', 'N/A')}건")
            elif isinstance(raw_data, list):
                # 배열 구조
                self.ubase_data = raw_data
            else:
                print(f"[WARNING] 알 수 없는 데이터 구조: {type(raw_data)}")
                self.ubase_data = []
                return
            
            # 고객번호 인덱스 생성
            for record in self.ubase_data:
                # 각 필드를 개별적으로 처리
                customer_number = record.get('customer_number', '').strip()
                product_code = record.get('상품코드', '').strip()
                korean_customer_no = record.get('고객번호', '').strip()
                
                # 모든 유효한 키를 인덱스에 추가
                if customer_number:
                    self.customer_index[customer_number] = record
                if product_code:
                    self.customer_index[product_code] = record
                if korean_customer_no:
                    self.customer_index[korean_customer_no] = record
            
            print(f"[SUCCESS] Ubase 데이터 로드: {len(self.ubase_data)}건, 고객번호 인덱스: {len(self.customer_index)}건")
            
        except FileNotFoundError:
            print(f"[ERROR] {self.ubase_file} 파일을 찾을 수 없습니다.")
        except Exception as e:
            print(f"[ERROR] Ubase 데이터 로드 오류: {e}")
            import traceback
            print(f"[ERROR] 상세 오류: {traceback.format_exc()}")
    
    def get_product_name_by_customer(self, customer_number: str) -> Optional[str]:
        """고객번호로 상품명 조회"""
        if not customer_number:
            return None
        
        record = self.customer_index.get(customer_number.strip())
        if record:
            # 다양한 필드명 지원
            product_name = (
                record.get('product_name', '') or 
                record.get('상품명', '') or 
                record.get('PGM명', '') or
                ''
            )
            return product_name if product_name else None
        return None
    
    def get_agent_response_by_customer(self, customer_number: str) -> Optional[str]:
        """고객번호로 상담원 답변 조회"""
        if not customer_number:
            return None
        
        record = self.customer_index.get(customer_number.strip())
        if record:
            # 다양한 필드명 지원
            agent_response = (
                record.get('agent_response', '') or 
                record.get('상담원답변', '') or 
                record.get('답변', '') or
                record.get('CS답변', '') or
                ''
            )
            
            # conversation_parsed 구조 확인
            conversation_parsed = record.get('conversation_parsed', {})
            if isinstance(conversation_parsed, dict) and 'agent' in conversation_parsed:
                agent_response = conversation_parsed['agent']
            
            return agent_response if agent_response else None
        return None
    
    def replace_template_placeholders_with_product(self, 
                                                 template_text: str, 
                                                 user_query: str = "",
                                                 customer_number: str = "",
                                                 context: str = "",
                                                 product_name: str = None) -> str:
        """템플릿 플레이스홀더 치환"""
        if not template_text:
            return template_text
        
        result = template_text
        original_result = result  # 원본 보존
        
        # 상품명이 제공되지 않았다면 고객번호로 조회
        if not product_name and customer_number:
            product_name = self.get_product_name_by_customer(customer_number)
        
        # 상품명 치환
        if product_name:
            # 상품명 플레이스홀더 패턴들 (정확한 플레이스홀더만)
            placeholders = [
                r'★',  # 가장 일반적인 패턴
                r'\{product_name\}',
                r'\[product_name\]',
                r'\[\{product_name\}\]',
                r'\{상품명\}',
                r'\[상품명\]',
                r'\[해당상품명\]',
                r'\{해당상품명\}',
                r'해당상품명'
            ]
            
            for placeholder in placeholders:
                result = re.sub(placeholder, product_name, result, flags=re.IGNORECASE)
        
        # 기타 플레이스홀더 치환
        replacements = {
            r'\{user_query\}': user_query or '문의내용',
            r'\{customer_number\}': customer_number or '고객번호',
            r'\{context\}': context or '상담유형',
            r'\{고객명\}': '고객님',
            r'\{날짜\}': '오늘',
        }
        
        for pattern, replacement in replacements.items():
            if re.search(pattern, result, flags=re.IGNORECASE):
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result
    
    def ultimate_product_name_fix(self, text: str, product_name: str = "") -> str:
        """최종 완벽한 상품명 치환"""
        if not text:
            return ""
        
        result = text
        
        # 1. product_name이 있으면 직접 치환
        if product_name and len(product_name.strip()) > 2:
            # 대괄호 제거한 버전도 만들기
            clean_name = re.sub(r'[\[\]()]', '', product_name).strip()
            
            # 여러 버전으로 치환 시도
            patterns_to_try = [
                re.escape(product_name),
                re.escape(clean_name),
                # 부분 매칭도 시도
                re.escape(product_name.replace('[', '').replace(']', ''))
            ]
            
            for pattern in patterns_to_try:
                if len(pattern) > 5:  # 너무 짧은 패턴 제외
                    result = re.sub(pattern, '★', result, flags=re.IGNORECASE)
        
        # 2. 대괄호 전체 치환
        bracket_patterns = [
            r'\[[^\]]*(?:세트|팩|박스|개입|ml|g|kg|L|호|번|정|원|％|%)[^\]]*\]',
            r'\[[^\]]{10,}\]'  # 긴 대괄호 내용
        ]
        
        for pattern in bracket_patterns:
            result = re.sub(pattern, '★', result)
        
        # 3. "★ 남은상품명" 패턴 완전 제거
        patterns_to_clean = [
            r'★\s+[가-힣A-Za-z0-9\s\(\)\-_+&]+(?:세트|팩|박스|개입|크림|로션|세럼|토너|클렌저|가디건|블라우스|팬츠|드레스|스커트|원피스)',
            r'★\s+[가-힣A-Za-z0-9\s\(\)\-_+&]{5,50}(?=\s+상품)',
            r'★\s+[가-힣A-Za-z0-9\s\(\)\-_+&]+\s+3pcs',
            r'★\s+[가-힣A-Za-z0-9\s\(\)\-_+&]{3,}(?=\s+(?:상품|제품|아이템))',
            r'★\s+[가-힣A-Za-z0-9\s\(\)\-_+&]{5,}',  # 일반적인 긴 텍스트
        ]
        
        for pattern in patterns_to_clean:
            result = re.sub(pattern, '★', result)
        
        # 4. 특수 케이스들 처리
        # "+블라우스+팬츠)" 같은 잔여물 제거
        result = re.sub(r'★\s*\+[가-힣]+\+[가-힣]+\)', '★', result)
        result = re.sub(r'★\s*[+][가-힣\s\(\)]+', '★', result)
        
        # 5. 최종 정리
        result = re.sub(r'★+', '★', result)  # 여러 ★을 하나로
        result = re.sub(r'\s*★\s*', ' ★ ', result)  # ★ 주변 공백 정리
        result = re.sub(r'\s+', ' ', result).strip()  # 여러 공백을 하나로
        
        return result