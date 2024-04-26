FROM ubuntu:22.04

# install app dependencies
RUN apt-get update && apt-get install -y python3 python3-pip

COPY requirements.txt /
RUN pip install --no-cache-dir -r requirements.txt

RUN apt install curl -y
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
RUN install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
RUN pip install kubernetes

# Add Docker's official GPG key:
RUN apt-get update
RUN apt-get install ca-certificates curl
RUN install -m 0755 -d /etc/apt/keyrings
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
RUN chmod a+r /etc/apt/keyrings/docker.asc


# Add the repository to Apt sources:
RUN echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null
RUN apt-get update
RUN apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y

RUN apt-get install -y systemctl
VOLUME /var/run/docker.sock 

# copy the flask app
COPY hello.py /
# COPY main.py /
COPY templates/ /templates/
COPY config.yaml /
COPY deploy_app.yaml /

# final configuration and running the application
ENV FLASK_APP=hello
EXPOSE 4444
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "4444"]
