from flask import Flask, request, render_template
import subprocess
import os
import json
from kubernetes import client, config
from kubernetes.stream import stream

app = Flask(__name__)
config.load_kube_config(config_file='config.yaml')
v1 = client.CoreV1Api()
namespace = 'deafult'
apps_v1 = client.AppsV1Api()
func_list = []

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def generate_dockerfile(function_name):
    dockerfile_content = f"""
    FROM ubuntu:22.04
    RUN apt-get update && apt-get install -y python3 python3-pip

    COPY uploads/{function_name}/requirements.txt /
    RUN pip install --no-cache-dir -r requirements.txt

    COPY uploads/{function_name}/{function_name}.py /
    EXPOSE 4444

    CMD ["bash", "-c","sleep infinity"]
    """

    with open(f'Dockerfile_{function_name}', 'w') as f:
        f.write(dockerfile_content)


def build_docker_image(function_name):
    o = subprocess.check_output(f"docker build -t chanikya1409/{function_name}-image -f Dockerfile_{function_name} ." ,shell=True, universal_newlines=True)
    o = subprocess.check_output(f"docker login -u chanikya1409 -p Prakash@123",shell=True, universal_newlines=True)
    o = subprocess.check_output(f"docker push chanikya1409/{function_name}-image:latest" ,shell=True, universal_newlines=True)
    
    return function_name


def deploy_function(fn_name, image_name, portnum):
    print(f"Reached Here: {fn_name}")
    try:
        print(image_name)
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
                    "name": fn_name,
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
            namespace='default',
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
        v1.create_namespaced_service(namespace='default',body=service_body)    
    except Exception as e:
            return f"service error: {e}"
    func_list.append(fn_name)
    
    return "Function registered successfully"
    
    
@app.route('/', methods=['GET', 'POST'])
def index():
        if request.method == 'GET':
            print(func_list)
            return render_template('index.html', names=func_list)
        else:
             return "POST request received"

@app.route('/function/<name>', methods=['GET', 'POST'])
def show_name(name):
    if request.method == 'GET':
        return render_template('fn.html', name=name)
    if request.method == 'POST':
        args = json.loads(request.form['args'])
        deployment = apps_v1.read_namespaced_deployment(name=name, namespace='default')
        selector = deployment.spec.selector.match_labels
        pod_list = v1.list_namespaced_pod(namespace='default', label_selector=','.join([f"{key}={val}" for key, val in selector.items()]))
        running_pods = [pod.metadata.name for pod in pod_list.items if pod.status.phase == "Running"]
        if running_pods:
            pod_name = running_pods[0]
            # print(pod_name)
            # Specify the command to execute
            arg_string = ','.join([f"{key}={val}" for key, val in args.items()])
            command = ["python3", "-c", f"from {name} import {name}; print({name}({arg_string}))"]
            # print(command[0])
            # Stream for converting to websocket and getting the response from kubectl
            exec_response = stream(v1.connect_get_namespaced_pod_exec,
                name=pod_name,
                namespace='default',
                command=command,
                stderr=True,
                stdin=True,
                stdout=True,
                tty=False,
            )
            print(exec_response[0])
            return exec_response  
        else:
            return "'error': 'No running pods found for the deployment'"       

@app.route('/register-docker', methods=['GET', 'POST'])
def register_docker():
    if request.method == 'POST':
        try:
            image_name = request.form['dockerimg']
            fn_name = request.form['fnname']
            o = subprocess.check_output("docker pull "+str(image_name) ,shell=True, universal_newlines=True)
            output = subprocess.check_output("docker inspect --format='{{range $p, $conf := .Config.ExposedPorts}}{{$p}}{{end}}' "+str(image_name),  shell=True, universal_newlines=True)
            portnum = output.split('/')[0]
            print(portnum)
        except Exception as e:
             return f"first Unexpected error: {e}"
        msg = deploy_function(fn_name, image_name, portnum)
        return msg  

@app.route('/register-python', methods=['GET', 'POST'])
def register_python():
    # Logic for registering function via Python file
    if request.method=="POST":
        fn_name = request.form['fnname']
        print(request.form)
        if 'fnfile' not in request.files:
            return 'No python code'
        if 'fnreqs' not in request.files:
            return 'No requirement file'
        
        fn_file = request.files['fnfile']
        fn_req = request.files['fnreqs']
        
        if fn_file.filename == '':
            return 'No selected file'
        
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], fn_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            
        # Save the file to a desired location
        fn_file.save(os.path.join(folder_path, fn_file.filename))
        fn_req.save(os.path.join(folder_path, fn_req.filename))
        # Create an empty requirements.txt if it doesn't exist -- not done yet
        generate_dockerfile(fn_name)
        build_docker_image(fn_name)
        print("fn name = ",fn_name)
        print("image name = ",fn_name + "-image:latest")
        msg = deploy_function(fn_name, "chanikya1409/"+fn_name + "-image:latest", 4444)
        return msg

if __name__ == '__main__':
    app.run(debug=False)
