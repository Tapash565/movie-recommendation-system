FROM continuumio/miniconda3:latest
WORKDIR /app
COPY . /app 
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8501"]