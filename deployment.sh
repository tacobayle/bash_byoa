#!/bin/bash
#
# this script will auto populate x amount of byoa deployment.
# this script will auto destroy deployment which contains destroy.do within the folder
# prerequisites:
# - git clone https://github.com/tacobayle/bash_byoa
# - cd bash_byoa
# - git clone https://github.com/tacobayle/byoa
# crontab -l
# * * * * * /home/ubuntu/bash_byoa/byoa.sh >>/home/ubuntu/bash_byoa/`date +\%Y\%m\%d`-byoa.log 2>&1
#
amount_of_available_deployment="4"
max_deployment="10"
subnet_base="10.1."
template_file=vcenter.json
source /home/ubuntu/.profile
#
tf_init_apply () {
  # $1 is the log path file for tf stdout
  # $2 is the log path file for tf error
  # $3 is var-file to feed TF with variables
  terraform init > $1 2>$2
  if [ -s "$2" ] ; then
    echo "TF Init ERRORS:"
    cat $2
    temp_id=$(basename $(pwd) | awk -F'_' '{print $3}')
    curl -X POST -H 'Content-type: application/json' --data '{"text":"Deployment id '$(echo $temp_id)' TF init failed"}' $SLACK_WEBHOOK_BYOA
    exit 1
  else
    rm $1 $2
  fi
  terraform apply -auto-approve -var-file=$3 > $1 2>$2
  if [ -s "$2" ] ; then
    echo "TF Apply ERRORS:"
    cat $2
    temp_id=$(basename $(pwd) | awk -F'_' '{print $3}')
    curl -X POST -H 'Content-type: application/json' --data '{"text":"Deployment id '$(echo $temp_id)' TF apply failed"}' $SLACK_WEBHOOK_BYOA
    exit 1
  fi
}
tf_destroy () {
  # $1 is the log path file for tf stdout
  # $2 is the log path file for tf error
  # $3 is var-file to feed TF with variables
  terraform destroy -auto-approve -var-file=$3 > $1 2>$2
  if [ -s "$2" ] ; then
    echo "TF Apply ERRORS:"
    cat $2
    temp_id=$(basename $(pwd) | awk -F'_' '{print $3}')
    curl -X POST -H 'Content-type: application/json' --data '{"text":"Deployment id '$(echo $temp_id)' destroy failed"}' $SLACK_WEBHOOK_BYOA
    exit 1
  fi
}
#
#
#
cd /home/ubuntu/bash_byoa
#
# Check for deployment(s) to destroy
#
while read line ; do
  if [ "$line" != "" ] ; then
    if [ ! -f $line/deployment.destroying ]; then
      cd $line
      touch deployment.destroying
      echo "$(date): Destroying deployment basic-ako id '$(echo $line | awk -F'_' '{print $3}')'"
      $(terraform output -json | jq -r .Destroy_command_wo_tf.value) > ansible_destroy.stdout 2>ansible_destroy.stderr
      tf_destroy destroy.stdout destroy.stderr vcenter.json
      cd - >/dev/null
      rm -fr $line
      echo "$(date): Deployment basic-ako id '$(echo $line | awk -F'_' '{print $3}')' fully destroyed"
    fi
  fi
done <<< "$(ls -d -1 byoa_deleting_* 2> /dev/null)"
#
# Check for max deployment(s)
#
if [ $(ls -d -1 byoa_*_* 2> /dev/null | grep . | wc -l) -lt $max_deployment ] ; then
  rm -f max
fi
#
# Check for deployment(s) to deploy
#
let amount_deployment=$(ls -d -1 byoa_deploying_* 2> /dev/null | grep . | wc -l)+$(ls -d -1 byoa_available_* 2> /dev/null | grep . | wc -l)
#
if [ $amount_deployment -ge $amount_of_available_deployment ] ; then
  echo "$(date): Available deployments: OK"
else
  echo "$(date): Available deployments: NOK"
  if [ $(ls -d -1 byoa_*_* 2> /dev/null | grep . | wc -l) -ge $max_deployment ] ; then
    touch max
    echo "$(date): Max deployment reached - need to wait"
  else
    echo "$(date): New deployment to be deployed"
    # determine which id to use for new deployment
    for deployment_id in $(seq 1 $max_deployment)
    do
      duplicate=0
      while read line ; do
        used_id=$(echo $line | awk -F'_' '{print $3}'| awk -F':' '{print $1}')
        if [ "$deployment_id" = "$used_id" ] ; then
          duplicate=1
        fi
      done <<< "$(ls -d -1 byoa_*_* 2> /dev/null | grep .)"
      if [ "$duplicate" -eq 0 ] ; then
        break
      fi
    done
    echo "$(date): deployment id to be used: $deployment_id"
    cp -r byoa byoa_deploying_$deployment_id
    cidr=$subnet_base$deployment_id.0/24
    contents="$(jq '.vcenter.folder = "'byoa_basic_ako_$deployment_id'" |
           .vcenter.vip_network.cidr = "'$cidr'" ' byoa_deploying_$deployment_id/$template_file)"
    echo "${contents}" | tee byoa_deploying_$deployment_id/$template_file > /dev/null
    cd byoa_deploying_$deployment_id
    echo "$(date): Deploying deployment basic-ako id $deployment_id"
    tf_init_apply deploy.stdout deploy.stderr vcenter.json
    tf_output=$(terraform output -json | jq 'del(.Destroy_command_all)' | jq 'del(.Destroy_command_wo_tf)')
    echo $tf_output | jq -r '. | keys[]' | while read line
    do
      echo $line | tee -a deployment.info > /dev/null
      echo $tf_output | jq -r .${line}.value | tee -a deployment.info > /dev/null
      echo "-----------" | tee -a deployment.info > /dev/null
    done
    cd - >/dev/null
    mv byoa_deploying_$deployment_id byoa_available_$deployment_id
    echo "$(date): Deployment basic-ako id $deployment_id fully deployed"
  fi
fi