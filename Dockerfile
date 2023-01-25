FROM python:3.11

RUN pip install -U pip
ADD . /traderev.flask
WORKDIR /traderev.flask
RUN pip install -r requirements.txt
ARG MONGO_FILE
ENV MONGO_INI=${MONGO_FILE}
RUN echo "MONGO_INI set to ${MONGO_INI}"
EXPOSE 5000
CMD ["./launcher.sh"]