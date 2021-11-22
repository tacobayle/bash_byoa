#!/usr/bin/env python3
from jinja2 import Template
import sys, json, yaml
import subprocess
import socket
from flask import Flask
from flask_restful import Api, Resource, reqparse, abort
#
# create command:
# curl -X PUT -H "Content-Type: application/json" -d '{"username":"nbayle"}' -w "HTTP response code: %{http_code}\n" http://127.0.0.1:5000/deployment-basic-ako
# worker = fqdn du worker
# $arcade_username
# delete command:
# curl -X DELETE -H "Content-Type: application/json" -d '{"username":"nbayle"}' -w "HTTP response code: %{http_code}\n" http://127.0.0.1:5000/deployment-basic-ako
# get command:
# curl -X GET -H "Content-Type: application/json" -d '{"username":"nbayle"}' -w "HTTP response code: %{http_code}\n" http://127.0.0.1:5000/deployment-basic-ako

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
    results_item_raw = subprocess.run(['ls'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    results_item = results_item_raw.stdout.decode("utf-8").split("\n")
    for repo in results_item:
      if repo.startswith('byoa_' + args['username']):
        username_repo = repo
        break
    else:
      abort(404, message='Unable to delete deployment called: ' + args['username'] + ' // folder not found')
    folder = username_repo
#     result_tf_output_raw = subprocess.run(['terraform', 'output', '-json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=folder)
#     result_tf_output = json.loads(result_tf_output_raw.stdout.decode("utf-8"))
#     for key in result_tf_output:
#       del result_tf_output[key]['sensitive']
#       del result_tf_output[key]['type']
#     del result_tf_output['Destroy_command_all']
#     del result_tf_output['Destroy_command_wo_tf']
#     return json.dumps(result_tf_output), 200
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 1))
    local_ip_address = s.getsockname()[0]
    return {'message': 'ssh ' + args['username'] + '@' + local_ip_address + '\nPassword is: ' + args['username']}, 201
#     result_tf_output_raw = subprocess.run(['terraform', 'output', '-json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=folder)

  def put(self):
    args = deploy_args.parse_args()
    results_item_raw = subprocess.run(['ls'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    results_item = results_item_raw.stdout.decode("utf-8").split("\n")
    if 'max' in results_item:
      abort(429, message='No resource available')
    for repo in results_item:
      if args['username'] in repo:
        abort(429, message= args['username'] + ' has already a deployment, please delete your deployment first')
        break
    else:
      for repo in results_item:
        if repo.startswith('byoa_available_'):
          available_repo = repo
          break
      else:
        abort(429, message= 'Wait few minutes to have a deployment available')
      folder = 'byoa_' + args['username'] + '_' + available_repo.split('_')[2]
      result_id = subprocess.run(['id', '-u', args['username']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      if result_id.returncode != 0:
        userdel = subprocess.run(['sudo', 'userdel', '-r', args['username']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        passwd_crypt = subprocess.run(['openssl', 'passwd', '-crypt', args['username']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        useradd = subprocess.run(['sudo', 'useradd', '-s', '/bin/bash', '-p', passwd_crypt.stdout.strip(), '-m', args['username']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['/bin/bash', 'account_customization.sh', args['username'], folder, available_repo.split('_')[2]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#         create_ssh_dir = subprocess.run(['sudo', 'runuser', '-l', args['username'], '-c', '\'mkdir /home/' + args['username'] + '/.ssh\''], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # sudo runuser -l nbayle -c 'mkdir /home/nbayle/.ssh'
#         result_id = subprocess.run(['id', '-u', args['username']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      # mv the repo
      subprocess.run(['mv', available_repo, folder], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#       result_tf_output_raw = subprocess.run(['terraform', 'output', '-json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=folder)
#       result_tf_output = json.loads(result_tf_output_raw.stdout.decode("utf-8"))
#       for key in result_tf_output:
#         del result_tf_output[key]['sensitive']
#         del result_tf_output[key]['type']
#       del result_tf_output['Destroy_command_all']
#       del result_tf_output['Destroy_command_wo_tf']
#       with open(folder + '/deployment.info', 'a') as file:
#         for key in result_tf_output:
#            file.write(key + ": \n")
#            file.write(str(result_tf_output[key]['value']))
#            file.write("\n-----------\n")
      return {'message': 'standard-ako deployment for ' + args['username'] + ' is deployed'}, 201

  def delete(self):
    args = deploy_args.parse_args()
    results_item_raw = subprocess.run(['ls'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    results_item = results_item_raw.stdout.decode("utf-8").split("\n")
    for repo in results_item:
      if repo.startswith('byoa_' + args['username']):
        username_repo = repo
        break
    else:
      abort(404, message='Unable to delete deployment for : ' + args['username'] + ' // folder not found')
    folder = username_repo
    subprocess.run(['mv', folder, folder.split('_')[0] + "_deleting_" + folder.split('_')[2]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(['sudo', 'userdel', '-r', args['username']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {'message': 'standard-ako deployment for ' + args['username'] + ' is deleting'}, 201


api.add_resource(deployment, "/deployment-basic-ako")
#
# Main Python script
#
if __name__ == '__main__':
  subnet_base="10.1."
#   byoa_ttl="86400"
  saml_user="nbayle"
  jinja2_file='/template/vcenter.j2'
  app.run(debug=True, host="0.0.0.0")
#   deployment_return=deploy(saml_user)
#
#   print(deployment_return)
#   destroy_return=destroy(saml_user)


#   saml_user="dwatson"
#   deployment_id=deploy_id(saml_user)
#   cidr=subnet_base+deployment_id+'.0/24'
#   print(cidr)
