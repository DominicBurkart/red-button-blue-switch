FROM pypy:3-6

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN set -ex; \
	apt-get update; \
	apt-get install -y --no-install-recommends \
        time

COPY . .

CMD ["pypy3", "./clean.py" ]