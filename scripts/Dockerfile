FROM python:3.9-alpine

WORKDIR /app/focusbuddy
RUN apk add --no-cache gcc g++ musl-dev linux-headers

COPY . .
RUN pip install --no-cache-dir -r ./requirements.txt
RUN pip install debugpy

CMD ["python", "./src/main.py"]
