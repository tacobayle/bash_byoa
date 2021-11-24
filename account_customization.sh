#!/bin/bash
# $1 is username
# $2 is the folder name of the deployment
# $3 is the id of the deployment
# $4 is the folder that contains the ssh key
# $5 is the clear password
sudo userdel -r $1
encrypted_password=$(openssl passwd -crypt $5)
sudo useradd -s /bin/bash -p $encrypted_password -m $1
sudo runuser -l $1 -c "/usr/bin/touch /home/${1}/.hushlogin"
sudo runuser -l $1 -c "/usr/bin/mkdir /home/${1}/.ssh"
sudo cp ${4}/ssh_private_key-byoa_basic_ako_${3}.pem /home/$1/.ssh/
sudo chown $1 /home/$1/.ssh/ssh_private_key-byoa_basic_ako_${3}.pem
sudo chgrp $1 /home/$1/.ssh/ssh_private_key-byoa_basic_ako_${3}.pem
sudo cp ${2}/ascii-art.ako-basic /home/${1}/ascii-art.ako-basic
sudo cp ${2}/deployment.info /home/${1}/byoa_basic_ako.info
sudo chown $1 /home/${1}/byoa_basic_ako.info
sudo chgrp $1 /home/${1}/byoa_basic_ako.info
sudo chown $1 /home/${1}/ascii-art.ako-basic
sudo chgrp $1 /home/${1}/ascii-art.ako-basic
echo "deployment.info () {" | sudo runuser -l $1 -c 'tee -a /home/'${1}'/.bashrc' > /dev/null
echo "  cat /home/${1}/byoa_basic_ako.info" | sudo runuser -l $1 -c 'tee -a /home/'${1}'/.bashrc' > /dev/null
echo "}" | sudo runuser -l $1 -c 'tee -a /home/'${1}'/.bashrc' > /dev/null
#echo "echo \"====================================================================================\"" | sudo runuser -l $1 -c 'tee -a /home/'${1}'/.bashrc' > /dev/null
#echo "echo \"==============================DEPLOYMENT DETAILS====================================\"" | sudo runuser -l $1 -c 'tee -a /home/'${1}'/.bashrc' > /dev/null
#echo "echo \"====================================================================================\"" | sudo runuser -l $1 -c 'tee -a /home/'${1}'/.bashrc' > /dev/null
echo "cat /home/${1}/ascii-art.ako-basic" | sudo runuser -l $1 -c 'tee -a /home/'${1}'/.bashrc' > /dev/null
echo "echo \"\"" | sudo runuser -l $1 -c 'tee -a /home/'${1}'/.bashrc' > /dev/null
echo "cat /home/${1}/byoa_basic_ako.info" | sudo runuser -l $1 -c 'tee -a /home/'${1}'/.bashrc' > /dev/null
echo "echo \"====================================================================================\"" | sudo runuser -l $1 -c 'tee -a /home/'${1}'/.bashrc' > /dev/null
echo "echo \"use the command 'deployment.info' to display the deployment details above at anytime\"" | sudo runuser -l $1 -c 'tee -a /home/'${1}'/.bashrc' > /dev/null
#echo "echo \"====================================================================================\"" | sudo runuser -l $1 -c 'tee -a /home/'${1}'/.bashrc' > /dev/null
