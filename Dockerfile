FROM python:3.11

RUN pip install -U pip
ADD . /traderev.flask
WORKDIR /traderev.flask
RUN pip install -r requirements.txt

EXPOSE 5000

CMD gunicorn --worker-class gevent --workers 2 --bind 0.0.0.0:5000 wsgi:run --max-requests 1000 --timeout 5 --keep-alive 5 --log-level info