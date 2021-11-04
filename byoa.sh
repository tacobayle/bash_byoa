#!/bin/bash
#
# this script will auto populate vcenter.json file and deploy/destroy BYOA deployment
#
# prerequisites:
# - mkdir /byoa
# - chmod 777 /byoa
# - git clone https://github.com/tacobayle/bash_byoa
# - cd bash_byoa
# - git clone https://github.com/tacobayle/byoa
# crontab -l
# * * * * * /home/ubuntu/bash_byoa/byoa.sh >>/home/ubuntu/bash_byoa/`date +\%Y\%m\%d`-byoa.log 2>&1
#
subnet_base="10.1."
byoa_ttl="86400" # 1 day = 86400
cd bash_byoa
source /home/ubuntu/.profile
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
# Check for deployment(s) to deploy
#
ls -1 /byoa/byoa_deploy_* 2> /dev/null | while read line ; do
  sudo rm -f $line
  deployment_id=$(echo $line | awk -F'_' '{print $3}')-byoa
  deployment_name=$(echo $line | awk -F'_' '{print $3}')
  subnet_third_octet=$(echo $line | awk -F'_' '{print $4}')
  cidr=$subnet_base$subnet_third_octet.0/24
  cp -r byoa $deployment_id
  cd $deployment_id
  date +%s > time.log
  touch "/byoa/${deployment_name}.ongoing"
  template_file=vcenter.json
  contents="$(jq '.vcenter.folder = "'$deployment_id'" |
           .vcenter.vip_network.cidr = "'$cidr'" ' $template_file)"
  echo "${contents}" | tee vcenter.json > /dev/null
  tf_init_apply "Create AKO infra for ${deployment_name} at $(date)"  deploy.stdout deploy.errors vcenter.json
  date +%s > time.log
  rm -f "/byoa/${deployment_name}.ongoing"
  touch "/byoa/${deployment_name}.done"
  terraform output | tee -a "/byoa/${deployment_name}.done"
  cd ..
done
#
# Check for deployment(s) to destroy manually
#
ls -1 /byoa/byoa_destroy_* 2> /dev/null | while read line ; do
  sudo rm -f $line
  deployment_id=$(echo $line | awk -F'_' '{print $3}')-byoa
  deployment_name=$(echo $line | awk -F'_' '{print $3}')
  cd $deployment_id
  $(terraform output -json | jq -r .Destroy_command_wo_tf.value)
  tf_destroy "Destroy AKO infra for '${deployment_name}' at $(date)"  destroy.stdout destroy.errors vcenter.json
  cd ..
#  rm -fr $deployment_id
  rm -f "/byoa/${deployment_name}.done"
done
#
# Check for deployment(s) to destroy because of byoa_ttl
#
ls -1 -d -- *-byoa 2> /dev/null | while read line ; do
  cd $line
  starting_time=$(cat time.log)
  deployment_name=$(echo $line | awk -F'-' '{print $1}')
  let DIFF=$(date +%s)-$starting_time
  if [ "$DIFF" -gt "$byoa_ttl" ] ; then
        echo "ttl over: $DIFF. Destroy infra for $deployment_name will be performed in one minute from $(date)"
        touch "/byoa/byoa_destroy_${deployment_name}"
  fi
done