FROM python:3.10-alpine
ENV TG_TOKEN=$TG_TOKEN
ENV OWM_TOKEN=$OWM_TOKEN
WORKDIR /app
ADD main.py .
ADD requirements.txt .
RUN apk add build-base libffi-dev
RUN pip install -r requirements.txt 
RUN adduser app -h /app -u 1000 -g 1000 -DH
USER 1000
CMD ["python", "main.py"]