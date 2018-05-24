FROM python:3.6.5-alpine3.7

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python3", "./clean.py" ]