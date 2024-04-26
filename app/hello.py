from flask import Flask, request, render_template
import subprocess
import json
from kubernetes import client, config
from kubernetes.stream import stream

app = Flask(__name__)
config.load_kube_config(config_file='config.yaml')
v1 = client.CoreV1Api()
namespace = 'chanikya'
apps_v1 = client.AppsV1Api()
l = []
@app.route('/', methods=['GET', 'POST'])
def index():
        if request.method == 'GET':
            return render_template('index.html', names=l)
        else:
             return "POST request recieved"

@app.route('/Function/<name>', methods=['GET', 'POST'])
def show_name(name):
    if request.method == 'GET':
        return render_template('fn.html', name=name)
    if request.method == 'POST':
        args = json.loads(request.form['args'])
        deployment = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
        selector = deployment.spec.selector.match_labels
        pod_list = v1.list_namespaced_pod(namespace=namespace, label_selector=','.join([f"{key}={val}" for key, val in selector.items()]))
        running_pods = [pod.metadata.name for pod in pod_list.items if pod.status.phase == "Running"]
        if running_pods:
            pod_name = running_pods[0]
            print(pod_name)
            # Specify the command to execute
            arg_string = ','.join([f"{key}={val}" for key, val in args.items()])
            command = ["python3", "-c", f"from {name} import {name}; print({name}({arg_string}))"]
            print(command)
            # Stream for converting to websocket and getting the response from kubectl
            exec_response = stream(v1.connect_get_namespaced_pod_exec,
                name=pod_name,
                namespace=namespace,
                command=command,
                stderr=True,
                stdin=True,
                stdout=True,
                tty=False,
            )
            return exec_response  
        else:
            return "'error': 'No running pods found for the deployment'"
        # pod_name = pod_list.items[0].metadata.name  
       

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
                    "containerPort": int(portnum)
                    }
                ]
                }
            ]
            }
        }
        }
    }
            
            apps_v1.create_namespaced_deployment(
                namespace=namespace,
                body=deploy_body
            )
        except Exception as e:
             return f"app deploy error: {e}, {deploy_body}"        
        try:
            service_body = {
        "kind": "Service",
        "apiVersion": "v1",
        "metadata": {
        "name": 'service'+fn_name
        },
        "spec": {
        "selector": {
            "app": fn_name
        },
        "ports": [
            {
            "name": "http",
            "protocol": "TCP",
            "port": int(portnum),
            "targetPort": int(portnum)
            }
        ]
        }
    }
            v1.create_namespaced_service(namespace=namespace, body=service_body)    
        except Exception as e:
             return f"service error: {e}"
    
    l.append(fn_name)
    return "Success"   
@app.route('/register-python')
def register_python():
    # Logic for registering function via Python file
    return "Function registered via Python file!"

if __name__ == '__main__':
    app.run(debug=True)
