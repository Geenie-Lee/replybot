pkill -9 -f gunicorn

nohup gunicorn --workers 2 --timeout 60 --bind 0.0.0.0:5000 web_server:app --access-logfile ./logs/app_$(date +%Y%m%d).log --error-logfile ./logs/app_$(date +%Y%m%d).log &

tail -f ./logs/app_20260306.log


ps -ef | grep python

nohup python portal_mock.py > ./logs/portal_$(date +%Y%m%d).log 2>&1 &

tail -f ./logs/portal_20260306.log
