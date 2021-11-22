#!/bin/bash
# $1 is username
# $2 is the folder name of the deployment
# $3 is the id of the deployment
sudo runuser -l $1 -c "/usr/bin/mkdir /home/${1}/.ssh"
sudo cp ssh_private_key-byoa_basic_ako_${3}.pem /home/$1/.ssh/
sudo chown $1 /home/$1/.ssh/ssh_private_key-byoa_basic_ako_${3}.pem
sudo chgrp $1 /home/$1/.ssh/ssh_private_key-byoa_basic_ako_${3}.pem
sudo cp ${2}/deployment.info /home/${1}/byoa_basic_ako.info
sudo chown $1 /home/${1}/byoa_basic_ako.info
sudo chgrp $1 /home/${1}/byoa_basic_ako.info
echo "deployment.info () {" | tee -a /home/${1}/.profile > /dev/null
echo "  cat /home/${1}/byoa_basic_ako.info" | tee -a /home/${1}/.profile > /dev/null
echo "}" | tee -a /home/${1}/.profile > /dev/null
echo "echo \"======================================================\"" | tee -a /home/${1}/.bashrc > /dev/null
echo "echo \"===============DEPLOYMENT DETAILS=====================\"" | tee -a /home/${1}/.bashrc > /dev/null
echo "echo \"======================================================\"" | tee -a /home/${1}/.bashrc > /dev/null
echo "cat /home/${1}/byoa_basic_ako.info" | tee -a /home/${1}/.bashrc > /dev/null
echo "echo \"======================================================\"" | tee -a /home/${1}/.bashrc > /dev/null
echo "echo \"======================================================\"" | tee -a /home/${1}/.bashrc > /dev/null
echo "echo \"use the command 'deployment.info' to display the deployment details\"" | tee -a /home/${1}/.bashrc
