#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import telegram
import urllib

TOKEN="176032236:AAF6h2YjwtUfsLP5K5O5wD8xV2dg3VadL5k"

b=telegram.Bot(TOKEN)

u=b.getUpdates()
lu = u[-1]

chat_id = lu.message.chat_id

url = "http://img03.deviantart.net/eb2d/i/2016/010/d/9/our_milky_way_by_deibiddonz-d9neuo6.jpg"
b.sendPhoto(chat_id=chat_id,photo=open("dice2.png",'rb'),caption="test_send_pic")
# b.sendPhoto(chat_id=chat_id,photo=urllib.request.urlopen(url),caption="test_send_pic_url")#doesn't work
