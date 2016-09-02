#!/bin/bash

cd `dirname $0`

mkdir links
touch links/DB_public_link

mkdir tokens
touch tokens/token
echo "0
0
" >  tokens/dropbox_tokens

mkdir env
#create environment
virtualenv env
# install dependencies
env/bin/python3 env/bin/pip3 install -r requirements.txt

echo "#!/bin/bash

env/bin/python3 Picture_Sender_Bot.py

exit 0
" > run.sh

chmod +x run.sh

exit 0