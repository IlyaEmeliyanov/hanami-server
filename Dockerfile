FROM python:3.7
WORKDIR /app

COPY . /app
RUN pip install --no-cache-dir -r ./requirements.txt

ENV DB_USERNAME=ilya
ENV DB_PASSWORD=hamare
ENV DB_CLUSTER=cluster0.a7d4nxo.mongodb.net
ENV DB_COLLECTION_NAME=hamare

ENV SERVER_URL=http://127.0.0.1
ENV SERVER_PORT=5500

ENV WS_URL=http://localhost:3000/
ENV WS_USERNAME=a
ENV WS_PASSWORD=a
ENV MAX_DISHES=5

EXPOSE 5500
CMD ["python3", "main.py"]
