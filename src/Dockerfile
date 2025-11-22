FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
# Important : Flask doit écouter sur 0.0.0.0 pour être accessible par Nginx
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]