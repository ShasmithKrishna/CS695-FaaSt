from flask import Flask, request, render_template
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
        image_name = request.form['dockerimg']
        fn_name = request.form['fnname']
        apps_v1.create_namespaced_deployment()

@app.route('/register-python')
def register_python():
    # Logic for registering function via Python file
    return "Function registered via Python file!"

if __name__ == '__main__':
    app.run(debug=True)
