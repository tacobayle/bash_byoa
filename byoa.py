#!/usr/bin/env python3
from jinja2 import Template
import sys, json, yaml
import subprocess
#
#
#
def destroy(username):
  result_id = subprocess.run(['id', '-u', username], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  if result_id.returncode != 0:
    return('unable to retrieve user id for deployment called: byoa_' + username)
  folder='byoa_' + username
  result_tf_output = subprocess.run(['terraform', 'output', '-json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=folder)
  result_tf_output_json = json.loads(result_tf_output.stdout.decode("utf-8"))
  ansible_destroy_command = result_tf_output_json['Destroy_command_wo_tf']['value'].split(" ")
  result_ansible_destroy = subprocess.run(ansible_destroy_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=folder)
  result_tf_destroy = subprocess.run(['terraform', 'destroy', '-auto-approve', '-var-file=vcenter.json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=folder)
  if result_tf_destroy.returncode != 0:
    return('terraform destroy failed: ' + result_tf_destroy.stderr.decode("utf-8"))
  return('deployment called ' + folder + ' has been destroyed')
  remove_directory = subprocess.run(['rm', '-fr', folder], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  userdel = subprocess.run(['sudo', 'userdel', '-r', username], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#
#
#
def deploy(username):
  result_id = subprocess.run(['id', '-u', username], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#   print(result_id.returncode)
  if result_id.returncode != 0:
    userdel = subprocess.run(['sudo', 'userdel', '-r', username], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    passwd_crypt = subprocess.run(['openssl', 'passwd', '-crypt', username], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    useradd = subprocess.run(['sudo', 'useradd', '-s', '/bin/bash', '-p', passwd_crypt.stdout.strip(), '-m', username], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result_id = subprocess.run(['id', '-u', username], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  # Duplicate byoa repo
  folder='byoa_' + username
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
#   else:
#     return('terraform init passed: ' + result_tf_init.stdout.decode("utf-8"))
  # TF Apply
  result_tf_apply = subprocess.run(['terraform', 'apply', '-auto-approve', '-var-file=vcenter.json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=folder)
  if result_tf_apply.returncode != 0:
    return('terraform apply failed: ' + result_tf_apply.stderr.decode("utf-8"))
  result_tf_output = subprocess.run(['terraform', 'output', '-json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=folder)
  result_tf_output_json = json.loads(result_tf_output.stdout.decode("utf-8"))
  return(result_tf_output_json)
#   else:
#     return('terraform apply passed: ' + result_tf_apply.stdout.decode("utf-8"))


#   except subprocess.CalledProcessError as e:
#     userdel = subprocess.run(['sudo', 'userdel', '-r', username], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     passwd_crypt = subprocess.run(['openssl', 'passwd', '-crypt', username], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     useradd = subprocess.run(['sudo', 'useradd', '-s', '/bin/bash', '-p', passwd_crypt.stdout.strip(), '-m', username], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     result_id = subprocess.run(['id', '-u', username], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     id = str(int(result_id.stdout.decode("utf-8")[-2:]))
#     return(id)
#   result_copy = subprocess.run(['cp', '-r', 'byoa', 'byoa_' + username], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#   result_tf_init = subprocess.run(['terraform', 'init'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd='byoa_' + username)


    # cp -r byoa $deployment_id
#
# Main Python script
#
if __name__ == '__main__':
  subnet_base="10.1."
#   byoa_ttl="86400"
  saml_user="nbayle"
  jinja2_file='/template/vcenter.j2'
  deployment_return=deploy(saml_user)
#
#   print(deployment_return)
#   destroy_return=destroy(saml_user)


#   saml_user="dwatson"
#   deployment_id=deploy_id(saml_user)
#   cidr=subnet_base+deployment_id+'.0/24'
#   print(cidr)
