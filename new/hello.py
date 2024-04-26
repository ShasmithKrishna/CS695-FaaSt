from flask import Flask, request, render_template
import subprocess
from kubernetes import client, config
app = Flask(__name__)
config.load_kube_config(config_file='config.yaml')
v1 = client.CoreV1Api()
namespace = 'chanikya'
apps_v1 = client.AppsV1Api()

@app.route('/', methods=['GET', 'POST'])
def index():
        if request.method == 'GET':
            return render_template('index.html')
        else:
             return "POST request recieved"

@app.route('/register-docker', methods=['GET', 'POST'])
def register_docker():
    if request.method == 'POST':
        try:
            image_name = request.form['dockerimg']
            fn_name = request.form['fnname']
            o = subprocess.check_output("docker pull "+str(image_name) ,shell=True, universal_newlines=True)
            output = subprocess.check_output("docker inspect --format='{{range $p, $conf := .Config.ExposedPorts}}{{$p}}{{end}}' "+str(image_name),  shell=True, universal_newlines=True)
            portnum = output.split('/')[0]
        except Exception as e:
             return f"first Unexpected error: {e}"
        try:
            deploy_body = {
        "kind": "Deployment",
        "apiVersion": "apps/v1",
        "metadata": {
        "name": fn_name
        },
        "spec": {
        "replicas": 2,
        "selector": {
            "matchLabels": {
            "app": fn_name
            }
        },
        "template": {
            "metadata": {
            "labels": {
                "app": fn_name
            }
            },
            "spec": {
            "containers": [
                {
                "name": fn_name ,
                "image": image_name,
                "imagePullPolicy": "Always",
                "ports": [
                    {
                    "containerPort": portnum
                    }
                ]
                }
            ]
            }
        }
        }
    }
            # print(deploy_body)
            apps_v1.create_namespaced_deployment(
                namespace=namespace,
                body=deploy_body
            )
        except Exception as e:
             return f"app deploy error: {e}"        
        try:
            service_body = {
        "kind": "Service",
        "apiVersion": "v1",
        "metadata": {
        "name": "nodeservice-loadbal"
        },
        "spec": {
        "selector": {
            "app": fn_name
        },
        "ports": [
            {
            "name": "http",
            "protocol": "TCP",
            "port": portnum,
            "targetPort": portnum
            }
        ]
        }
    }
            v1.create_namespaced_service(namespace=namespace, body=service_body)    
        except Exception as e:
             return f"service error: {e}"   
@app.route('/register-python')
def register_python():
    # Logic for registering function via Python file
    return "Function registered via Python file!"

if __name__ == '__main__':
    app.run(debug=True)
