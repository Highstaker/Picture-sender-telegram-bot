#!/bin/bash

mkdir env
#create environment
virtualenv env/picbot_env
# install dependencies
env/picbot_env/bin/python3 env/picbot_env/bin/pip3 install -r requirements.txt

echo "#!/bin/bash

env/picbot_env/bin/python3 Picture_Sender_Bot.py

exit 0
" > run.sh

chmod +x run.sh

exit 0