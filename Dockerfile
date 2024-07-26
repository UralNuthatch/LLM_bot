FROM python:3.11-slim-bullseye
ENV PYTHONWRITEBYTECODE 1
ENV PYTHONBUFFERED 1
WORKDIR /LLM_bot
COPY . /LLM_bot
RUN apt update && apt-get install -y wget
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install -y ./google-chrome-stable_current_amd64.deb
RUN pip install --no-cache -r /LLM_bot/requirements.txt
CMD ["python", "-m", "main"]
