FROM pypy:3-6.0.0

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["pypy3", "./clean.py" ]