FROM demo-app:1.0.0

COPY requirements.txt .

CMD ["python","app.py"]