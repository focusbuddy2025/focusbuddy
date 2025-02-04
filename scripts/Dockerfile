FROM python:3.9-alpine

WORKDIR /app/focusbuddy

COPY . .
RUN pip install --no-cache-dir -r ./requirements.txt

CMD ["python", "./src/main.py"]
