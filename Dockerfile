FROM python:3.8-alpine

ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9

WORKDIR /chatbot

COPY ./ /chatbot

RUN pip install numpy
RUN pip install scipy
RUN pip install gensim==3.8.3
RUN pip install janome
RUN pip install Flask
RUN pip install Werkzeug
RUN pip install openpyxl

CMD ["python", "run.py"]
