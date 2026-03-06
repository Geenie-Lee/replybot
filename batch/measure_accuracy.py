import os
import sys
import json
import pickle
import traceback
import faulthandler

faulthandler.enable()

os.environ["OPENBLAS_CORETYPE"] = "SANDYBRIDGE"
os.environ["OMP_NUM_THREADS"] = "1"

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODEL_FILE = os.path.join(BASE_DIR, "model", "randomforest_model.pkl")
TEMPLATES_FILE = os.path.join(BASE_DIR, "model", "reply_templates_50.json")
SQL_FILE = os.path.join(BASE_DIR, "model", "cid_question4_2.sql")
SQL_OUT_FILE = os.path.join(BASE_DIR, "model", "cid_question4_2.sql")

def extract_morphological_keywords(text: str, kiwi_analyzer) -> list:
    if not text:
        return []
    keywords = []
    try:
        result = kiwi_analyzer.analyze(text)
        important_pos = {'NNG', 'NNP', 'VV', 'VA', 'VX', 'MM', 'MAG', 'NNB', 'XSV', 'XSA'}
        for token in result[0][0]:
            form = token.form
            pos = token.tag
            if pos in important_pos and len(form) >= 2:
                keywords.append(form)
            if len(form) >= 3:
                if pos in {'VV', 'VA', 'VX'}:
                    if form.endswith(('하다', '되다', '이다')):
                        base = form[:-2]
                        if len(base) >= 2:
                            keywords.append(base)
                elif pos in {'NNG', 'NNP'}:
                    if '취소' in form: keywords.append('취소')
                    if '반품' in form: keywords.append('반품')
                    if '교환' in form: keywords.append('교환')
                    if '배송' in form: keywords.append('배송')
                    if '환불' in form: keywords.append('환불')
                    if '변경' in form: keywords.append('변경')
        return keywords
    except Exception as e:
        return []

def main():
    log_file = open(os.path.join(BASE_DIR, "batch", "batch_debug.log"), "w", encoding="utf-8")
    def lg(msg):
        log_file.write(msg + "\n")
        log_file.flush()

    try:
        lg("Starting main...")
        lg("Importing external libraries inside main()...")
        import numpy as np
        import sklearn
        from sklearn.ensemble import RandomForestClassifier
        from kiwipiepy import Kiwi
        lg("Imports ok.")

        lg("Loading Kiwi...")
        kiwi_analyzer = Kiwi()

        lg("Loading templates...")
        with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
            templates_data = json.load(f)

        lg("Loading randomforest_model.pkl...")
        with open(MODEL_FILE, 'rb') as f:
            randomforest_classifier = pickle.load(f)

        lg(f"Loading SQL file: {SQL_FILE}")
        with open(SQL_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        if not lines:
            lg("빈 파일입니다.")
            return
            
        header = lines[0].rstrip("\n")
        data_lines = [l.rstrip("\n") for l in lines[1:] if l.strip()]
        data_lines = [l for l in data_lines if not l.startswith("전체 정확도")]
        
        parts = header.split('\t')
        if "answer_category_id" not in parts:
            new_header = header + "\tanswer_category_id"
        else:
            new_header = header
            
        new_lines = [new_header]
        
        category_ids = []
        questions = []
        texts_to_predict = []
        original_cols = []
        
        lg("문장 분석 진행 중...")
        for idx, line in enumerate(data_lines):
            cols = line.split('\t')
            try:
                category_id = int(cols[0])
            except ValueError:
                category_id = 0
                
            question = cols[1] if len(cols) > 1 else ""
            question_cleaned = question.replace('\\n', ' ')
            
            keywords = extract_morphological_keywords(question_cleaned, kiwi_analyzer)
            text_ready = ' '.join(keywords) if keywords else ""
            
            category_ids.append(category_id)
            questions.append(question)
            texts_to_predict.append(text_ready)
            original_cols.append(cols)
            
        lg(f"총 {len(texts_to_predict)}건 벡터화 시작...")
        
        vectorizer = randomforest_classifier['vectorizer']
        lg("transform start")
        X_tfidf = vectorizer.transform(texts_to_predict)
        lg("transform done")
        
        model = randomforest_classifier['model']
        if hasattr(model, 'n_jobs'):
            model.n_jobs = 1

        lg("predict start")
        predictions_labels = model.predict(X_tfidf)
        lg("predict done")
        
        correct_count = 0
        total_count = len(category_ids)
        
        lg("채점 진행 중...")
        for i in range(total_count):
            try:
                predicted_id = int(predictions_labels[i])
            except:
                predicted_id = 0
                
            actual_id = category_ids[i]
            if predicted_id == actual_id:
                correct_count += 1
                
            cols = original_cols[i]
            if len(cols) >= 3 and "answer_category_id" in header:
                cols[2] = str(predicted_id)
                new_row = '\t'.join(cols)
            else:
                new_row = f"{cols[0]}\t{cols[1] if len(cols)>1 else ''}\t{predicted_id}"
                
            new_lines.append(new_row)
            
        accuracy = correct_count / total_count if total_count > 0 else 0.0
        acc_msg = f"전체 정확도: {accuracy*100:.2f}% ({correct_count}/{total_count})"
        lg(acc_msg)
        
        new_lines.append(acc_msg)
        
        lg("결과 저장 중...")
        with open(SQL_OUT_FILE, 'w', encoding='utf-8') as f:
            for idx, nl in enumerate(new_lines):
                f.write(nl + ('\n' if idx < len(new_lines) - 1 else ''))
                
        lg("완료")
        print(acc_msg)
    except Exception as e:
        lg("에러 발생:")
        lg(traceback.format_exc())
    finally:
        log_file.close()

if __name__ == '__main__':
    main()
