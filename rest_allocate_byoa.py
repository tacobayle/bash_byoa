#!/usr/bin/env python3
from jinja2 import Template
import sys, json, yaml
import subprocess
from flask import Flask
from flask_restful import Api, Resource, reqparse, abort
#
# create command:
# curl -X PUT -H "Content-Type: application/json" -d '{"username":"nbayle"}' -w "HTTP response code: %{http_code}\n" http://127.0.0.1:5000/deployment-basic-ako
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
    result_tf_output_raw = subprocess.run(['terraform', 'output', '-json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=folder)
    result_tf_output = json.loads(result_tf_output_raw.stdout.decode("utf-8"))
    for key in result_tf_output:
      del result_tf_output[key]['sensitive']
      del result_tf_output[key]['type']
    return json.dumps(result_tf_output), 200

  def put(self):
    args = deploy_args.parse_args()
    results_item_raw = subprocess.run(['ls'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    results_item = results_item_raw.stdout.decode("utf-8").split("\n")
    if 'max' in results_item:
      abort(429, message='No resource available')
    for repo in results_item:
      if args['username'] in repo:
        abort(429, message='You already have a deployment')
        break
    else:
      for repo in results_item:
        if repo.startswith('byoa_available_'):
          available_repo = repo
          break
      else:
        print('Wait few minutes to have a deployment available')
      folder = 'byoa_' + args['username'] + '_' + available_repo.split('_')[2]
      result_id = subprocess.run(['id', '-u', args['username']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      if result_id.returncode != 0:
        userdel = subprocess.run(['sudo', 'userdel', '-r', args['username']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        passwd_crypt = subprocess.run(['openssl', 'passwd', '-crypt', args['username']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        useradd = subprocess.run(['sudo', 'useradd', '-s', '/bin/bash', '-p', passwd_crypt.stdout.strip(), '-m', args['username']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result_id = subprocess.run(['id', '-u', args['username']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      # mv the repo
      subprocess.run(['mv', available_repo, folder], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      result_tf_output = subprocess.run(['terraform', 'output', '-json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=folder)
      return {'deployment_type': 'standard-ako', 'status': 'deployed', 'username': args['username']}, 201

  def delete(self):
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
    subprocess.run(['mv', folder, folder.split('_')[0] + "_deleting_" + folder.split('_')[2]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {'deployment_name': args['username'], 'status': 'deleting'}, 204


api.add_resource(deployment, "/deployment-basic-ako")
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