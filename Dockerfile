FROM python:3.7-alpine
WORKDIR /src
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD ["python3", "src/app.py"]