FROM continuumio/miniconda3:latest
WORKDIR /app
COPY . /app 
RUN conda env create -f environment.yml
SHELL ["conda", "run", "-n", "venv", "/bin/bash", "-c"]
EXPOSE $PORT
CMD ["sh", "-c", "conda run --no-capture-output -n venv uvicorn app:app --host 0.0.0.0 --port $PORT --workers 1"]
