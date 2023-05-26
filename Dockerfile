
FROM python:3.8

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/
ENV DISPLAY=:99

COPY . /app
WORKDIR /app
RUN pip install --upgrade pip
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
