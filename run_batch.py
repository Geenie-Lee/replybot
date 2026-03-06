import traceback
try:
    with open('batch/measure_accuracy.py', encoding='utf-8') as f:
        code = f.read()
    exec(code, {'__file__': 'batch/measure_accuracy.py', '__name__': '__main__'})
except BaseException as e:
    with open("err.txt", "w", encoding='utf-8') as errf:
        errf.write(traceback.format_exc())
