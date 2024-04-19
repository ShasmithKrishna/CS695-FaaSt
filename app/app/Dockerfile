FROM ubuntu:22.04

# install app dependencies
RUN apt-get update && apt-get install -y python3 python3-pip

COPY requirements.txt /
RUN pip install --no-cache-dir -r requirements.txt

RUN apt install curl -y
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
RUN install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
# copy the flask app
COPY hello.py /
COPY templates/ /templates/
COPY config.yaml /
COPY deploy_app.yaml /

# final configuration and running the application
ENV FLASK_APP=hello
EXPOSE 8000
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "8000"]
