FROM python:3.7-alpine
WORKDIR /src
COPY . . 
RUN pip install -r requirements.txt
VOLUME ./data /data
CMD ["python3", "src/app.py"]