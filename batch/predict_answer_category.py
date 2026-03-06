import os
import sys
import pickle
import traceback
import faulthandler

faulthandler.enable()

os.environ["OPENBLAS_CORETYPE"] = "SANDYBRIDGE"
os.environ["OMP_NUM_THREADS"] = "1"

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODEL_FILE = os.path.join(BASE_DIR, "model", "randomforest_model.pkl")
INPUT_TSV = os.path.join(BASE_DIR, "model", "categoryid_question_260304.tsv")
OUTPUT_TSV = os.path.join(BASE_DIR, "model", "categoryid_question_260304.tsv") # Save over the same file or make a new one? The prompt says "추가해서... 추가해줘." We will overwrite it.

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
            # 복합어 분해
            if len(form) >= 3:
                # 동사/형용사 어간 추출
                if pos in {'VV', 'VA', 'VX'}:
                    if form.endswith(('하다', '되다', '이다')):
                        base = form[:-2]
                        if len(base) >= 2:
                            keywords.append(base)
                # 명사 복합어 처리
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
    print("Starting prediction process...")
    try:
        import numpy as np
        import sklearn
        from sklearn.ensemble import RandomForestClassifier
        from kiwipiepy import Kiwi

        print("Loading Kiwi...")
        kiwi_analyzer = Kiwi()

        print(f"Loading randomforest_model from {MODEL_FILE}...")
        with open(MODEL_FILE, 'rb') as f:
            randomforest_classifier = pickle.load(f)

        import csv
        
        print(f"Reading input file: {INPUT_TSV}")
        parsed_data = []
        header = []
        
        with open(INPUT_TSV, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f, delimiter='\t', quotechar='"')
            try:
                header = next(reader)
            except StopIteration:
                print("File is empty.")
                return
                
            for row in reader:
                if row:
                    parsed_data.append(row)

        has_answer_col = "answer_category_id" in header
        
        if not has_answer_col:
            header.append("answer_category_id")
            
        try:
            category_col_idx = header.index("category_id")
        except ValueError:
            category_col_idx = 0
            
        try:
            question_col_idx = header.index("question")
        except ValueError:
            question_col_idx = 1
            
        texts_to_predict = []

        print("Analyzing questions...")
        for cols in parsed_data:
            question = cols[question_col_idx] if len(cols) > question_col_idx else ""
            question_cleaned = question.replace('\n', ' ').replace('\\n', ' ').strip()
            
            keywords = extract_morphological_keywords(question_cleaned, kiwi_analyzer)
            text_ready = ' '.join(keywords) if keywords else ""
            
            texts_to_predict.append(text_ready)

        print(f"Vectorizing {len(texts_to_predict)} questions...")
        vectorizer = randomforest_classifier['vectorizer']
        X_tfidf = vectorizer.transform(texts_to_predict)

        print("Predicting categories...")
        model = randomforest_classifier['model']
        if hasattr(model, 'n_jobs'):
            model.n_jobs = 1

        predictions_labels = model.predict(X_tfidf)
        
        # Rule-based post-processing
        probabilities = model.predict_proba(X_tfidf)
        model_classes = model.classes_
        
        print("Saving predictions...")
        new_lines = []
        new_lines.append(header)
        
        match_count = 0
        total_count = len(parsed_data)
        
        for i in range(len(parsed_data)):
            try:
                predicted_id = str(int(predictions_labels[i]))
            except ValueError:
                predicted_id = str(predictions_labels[i])
                
            cols = parsed_data[i]
            question = cols[question_col_idx] if len(cols) > question_col_idx else ""
            
            target_category_id = str(cols[category_col_idx]).strip()
            
            # Post-processing matching logic from web_server.py
            if '변경' in question or '교환' in question:
                # Get index of current prediction
                try:
                    current_idx = np.where(model_classes == int(predicted_id))[0][0]
                except:
                    current_idx = None
                    
                pass
                
            if has_answer_col and len(cols) == len(header):
                # Update existing column
                cols[-1] = predicted_id
                new_row = cols
            else:
                # Add new column or append
                cols.append(predicted_id)
                new_row = cols
                
            new_lines.append(new_row)
            
            if target_category_id == predicted_id.strip():
                match_count += 1

        if total_count > 0:
            accuracy = (match_count / total_count) * 100
            print(f"Accuracy: {accuracy:.2f}% ({match_count}/{total_count})")
            
            accuracy_row = ["" for _ in range(len(header))]
            accuracy_row[0] = "Accuracy(정확도)"
            accuracy_row[-1] = f"{accuracy:.2f}%"
            new_lines.append(accuracy_row)

        print(f"Writing output to {OUTPUT_TSV}...")
        with open(OUTPUT_TSV, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerows(new_lines)
                
        print("Done!")

    except Exception as e:
        print("Error occurred:")
        traceback.print_exc()

if __name__ == '__main__':
    main()
