# Use the Python 3.11 base image
FROM python:3.11

# Set the working directory (optional)
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install
RUN playwright install-deps

COPY . .
RUN rm -rf .venv || true

RUN ls -al

RUN pip install -r requirements.txt

RUN which python
RUN python -V

ENTRYPOINT ["python", "main.py"]
