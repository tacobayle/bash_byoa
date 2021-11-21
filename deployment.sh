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
  # $1 messsage to display
  # $2 is the log path file for tf stdout
  # $3 is the log path file for tf error
  # $4 is var-file to feed TF with variables
  echo "---------------------------------------------------------------------------------"
  echo $1
  echo "---------------------------------------------------------------------------------"
  terraform init > $2 2>$3
  if [ -s "$3" ] ; then
    echo "TF Init ERRORS:"
    cat $3
    exit 1
  else
    rm $2 $3
  fi
  terraform apply -auto-approve -var-file=$4 > $2 2>$3
  if [ -s "$3" ] ; then
    echo "TF Apply ERRORS:"
    cat $3
    exit 1
  fi
}
tf_destroy () {
  # $1 messsage to display
  # $2 is the log path file for tf stdout
  # $3 is the log path file for tf error
  # $4 is var-file to feed TF with variables
  echo "---------------------------------------------------------------------------------"
  echo $1
  echo "---------------------------------------------------------------------------------"
  terraform destroy -auto-approve -var-file=$4 > $2 2>$3
  if [ -s "$3" ] ; then
    echo "TF Apply ERRORS:"
    cat $3
    exit 1
  fi
}
#
# Check for max deployment(s)
#
if [ $(ls -d -1 byoa_*_* 2> /dev/null | grep . | wc -l) -lt $max_deployment ] ; then
  rm -f max
fi
#
# Check for deployment(s) to destroy
#
while read line ; do
  if [ "$line" != "" ] ; then
    cd $line
    echo "line is: $line"
    $(terraform output -json | jq -r .Destroy_command_wo_tf.value)
    tf_destroy "Destroy deployment basic-ako id '$(echo $line | awk -F'_' '{print $3}')' at $(date)" destroy.stdout destroy.errors vcenter.json
    cd -
    rm -fr $line
  fi
done <<< "$(ls -d -1 byoa_deleting_* 2> /dev/null)"
#
# Check for deployment(s) to deploy
#
let amount_deployment=$(ls -d -1 byoa_deploying_* 2> /dev/null | grep . | wc -l)+$(ls -d -1 byoa_available_* 2> /dev/null | grep . | wc -l)
#
if [ $amount_deployment -ge $amount_of_available_deployment ] ; then
  echo "Available deployments: OK"
else
  echo "Available deployments: NOK"
  if [ $(ls -d -1 byoa_*_* 2> /dev/null | grep . | wc -l) -ge $max_deployment ] ; then
    touch max
    echo "Max deployment reached - need to wait"
  else
    echo "New deployment to be deployed"
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
    echo "deployment id to be used: $deployment_id"
    cp -r byoa byoa_deploying_$deployment_id
    cidr=$subnet_base$deployment_id.0/24
    contents="$(jq '.vcenter.folder = "'byoa_$deployment_id'" |
           .vcenter.vip_network.cidr = "'$cidr'" ' byoa_deploying_$deployment_id/$template_file)"
    echo "${contents}" | tee byoa_deploying_$deployment_id/$template_file > /dev/null
    cd byoa_deploying_$deployment_id
    tf_init_apply "Create AKO infra for deployment id: ${deployment_id} at $(date)"  deploy.stdout deploy.errors vcenter.json
    cd -
    mv byoa_deploying_$deployment_id byoa_available_$deployment_id
  fi
fi