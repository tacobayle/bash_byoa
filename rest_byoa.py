#!/usr/bin/env python3
from jinja2 import Template
import sys, json, yaml
import subprocess
from flask import Flask
from flask_restful import Api, Resource, reqparse, abort
#
# create command:
# curl -X PUT -H "Content-Type: application/json" -d '{"username":"nbayle"}' http://127.0.0.1:5000/deployment
# delete command:
# curl -X DELETE -H "Content-Type: application/json" -d '{"username":"nbayle"}' http://127.0.0.1:5000/deployment


app = Flask(__name__)
api = Api(app)
#
deploy_args = reqparse.RequestParser()
deploy_args.add_argument("username", type=str, help="Name of the deployment required", required=True)
#
#
class deployment(Resource):

  def get(self):
    args = deploy_args.parse_args()
    folder = 'byoa_' + args['username']
    list_deployments_string=subprocess.run(['ls'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    list_deployments = list_deployments_string.stdout.decode("utf8").split('\n')
    if folder not in list_deployments:
#       abort(404, message='Unable to get deployment called: ' + args['name'] + ' folder not found')
      status = 'does not exists'
    status = 'running'
#     full_deployment_name = 'byoa_' + args['name']
#     if full_deployment_name not in deployments:
#       abort(404, message='Could not find deployment called: ' + args['name'])
    return {'deployment_name': args['username'], 'status': status}, 201

  def put(self):
    args = deploy_args.parse_args()
    result_id = subprocess.run(['id', '-u', args['username']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result_id.returncode != 0:
      userdel = subprocess.run(['sudo', 'userdel', '-r', args['username']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      passwd_crypt = subprocess.run(['openssl', 'passwd', '-crypt', args['username']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      useradd = subprocess.run(['sudo', 'useradd', '-s', '/bin/bash', '-p', passwd_crypt.stdout.strip(), '-m', args['username']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      result_id = subprocess.run(['id', '-u', args['username']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Duplicate byoa repo
    folder='byoa_' + args['username']
    result_copy = subprocess.run(['cp', '-r', 'byoa', folder], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Populate vcenter.json
    deployment_id = str(int(result_id.stdout.decode("utf-8")[-2:]))
    cidr=subnet_base+deployment_id+'.0/24'
    json_variables = {'folder': folder, 'cidr': cidr}
    with open(folder + jinja2_file) as file_:
      t = Template(file_.read())
    final_json=t.render(json_variables)
    with open(folder + '/vcenter.json', 'w') as f:
      f.write(final_json)
    # TF init
    result_tf_init = subprocess.run(['terraform', 'init'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=folder)
    if result_tf_init.returncode != 0:
      return('terraform init failed: ' + result_tf_init.stderr.decode("utf-8"))
    # TF Apply
    result_tf_apply = subprocess.run(['terraform', 'apply', '-auto-approve', '-var-file=vcenter.json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=folder)
    if result_tf_apply.returncode != 0:
      return('terraform apply failed: ' + result_tf_apply.stderr.decode("utf-8"))
    result_tf_output = subprocess.run(['terraform', 'output', '-json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=folder)
    result_tf_output_json = json.loads(result_tf_output.stdout.decode("utf-8"))
#     return(result_tf_output_json)
    return {'deployment_name': args['username'], 'status': 'deployed'}, 201

#     return {result_tf_output_json}, 201




  def delete(self):
    args = deploy_args.parse_args()
    folder = 'byoa_' + args['username']
    list_deployments_string=subprocess.run(['ls'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    list_deployments = list_deployments_string.stdout.decode("utf8").split('\n')
    if folder not in list_deployments:
      abort(404, message='Unable to delete deployment called: ' + args['name'] + ' folder not found')
    result_tf_output = subprocess.run(['terraform', 'output', '-json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=folder)
    result_tf_output_json = json.loads(result_tf_output.stdout.decode("utf-8"))
    ansible_destroy_command = result_tf_output_json['Destroy_command_wo_tf']['value'].split(" ")
    result_ansible_destroy = subprocess.run(ansible_destroy_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=folder)
    result_tf_destroy = subprocess.run(['terraform', 'destroy', '-auto-approve', '-var-file=vcenter.json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=folder)
    if result_tf_destroy.returncode != 0:
      return('terraform destroy failed: ' + result_tf_destroy.stderr.decode("utf-8"))
#     return('deployment called ' + folder + ' has been destroyed')
    remove_directory = subprocess.run(['rm', '-fr', folder], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    userdel = subprocess.run(['sudo', 'userdel', '-r', args['username']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {'deployment_name': args['username'], 'status': 'deleted'}, 204


api.add_resource(deployment, "/deployment")
#
# Main Python script
#
if __name__ == '__main__':
  subnet_base="10.1."
#   byoa_ttl="86400"
  saml_user="nbayle"
  jinja2_file='/template/vcenter.j2'
  app.run(debug=True)
#   deployment_return=deploy(saml_user)
#
#   print(deployment_return)
#   destroy_return=destroy(saml_user)


#   saml_user="dwatson"
#   deployment_id=deploy_id(saml_user)
#   cidr=subnet_base+deployment_id+'.0/24'
#   print(cidr)
