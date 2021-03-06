#!/usr/bin/env python3
# coding: utf-8
import time
import wxpy
import logging
import re
import html

from . import config
from .slackbot_main import slackbot

slack_client = slackbot._client
wxbot = None

emoji_map_table = {
    '[Smile]': u'\U0001f600',
    '[Drool]': u'\U0001f60d',
    '[Scowl]': u'\U0001f633',
    '[Chill]': u'\U0001f60e',
    '[Sob]': u'\U0001f62d',
    '[Shy]': u'\U0000263a',
    '[Shutup]': u'\U0001f64a',
    '[Sleep]': u'\U0001f634',
    '[Cry]': u'\U0001f623',
    '[Awkward]': u'\U0001f630',
    '[Pout]': u'\U0001f621',
    '[Wink]': u'\U0001f61c',
    '[Grin]': u'\U0001f601',
    '[Surprised]': u'\U0001f631',
    '[Frown]': u'\U0001f62f',
    '[Scream]': u'\U0001f62b',
    '[Joyful]': u'\U0001f60a',
    '[Smug]': u'\U0001f615',
    '[Drowsy]': u'\U0001f62a',
    '[Panic]': u'\U0001f631',
    '[Sweat]': u'\U0001f613',
    '[Laugh]': u'\U0001f604',
    '[Loafer]': u'\U0001f60f',
    '[Strive]': u'\U0001f4aa',
    '[Scold]': u'\U0001f624',
    '[Doubt]': u'\U00002753',
    '[Dizzy]': u'\U0001f632',
    '[Skull]': u'\U0001f480',
    '[Relief]': u'\U0001f625',
    '[Clap]': u'\U0001f44f',
    '[Trick]': u'\U0001f47b',
    u'[Bah！L]': u'\U0001f63e',
    u'[Bah！R]': u'\U0001f63e',
    '[Yawn]': u'\U0001f62a',
    '[Lookdown]': u'\U0001f612',
    '[Puling]': u'\U0001f614',
    '[Sly]': u'\U0001f608',
    '[Kiss]': u'\U0001f618',
    '[Cleaver]': u'\U0001f52a',
    '[Melon]': u'\U0001f349',
    '[Beer]': u'\U0001f37a',
    '[Coffee]': u'\U00002615',
    '[Pig]': u'\U0001f437',
    '[Rose]': u'\U0001f339',
    '[Lip]': u'\U0001f48b',
    '[Heart]': u'\U00002764',
    '[BrokenHeart]': u'\U0001f494',
    '[Cake]': u'\U0001f382',
    '[Bomb]': u'\U0001f4a3',
    '[Poop]': u'\U0001f4a9',
    '[Moon]': u'\U0001f319',
    '[Sun]': u'\U0001f31e',
    '[Strong]': u'\U0001f44d',
    '[Weak]': u'\U0001f44e',
    '[Victory]': u'\U0001f31e',
    '[Fist]': u'\U0000270a',
    '[OK]': u'\U0001f44c',

}


def filter_text(text):
    for k, v in emoji_map_table.items():
        text = text.replace(k, v)
    while True:
        result = re.search('(<span class="emoji emoji([0-9a-f]*)"></span>)', text)
        if result:
            emoji = result.groups()[1]
            text = text.replace(result.groups()[0], ('\\U' + '0' * (8 - len(emoji)) + emoji).decode('unicode-escape'))
        else:
            break
    return text


def forward_msg_to_slack(msg, from_user, to_channel, from_group=None):
    place = ' in ' + from_group if from_group else ""
    if msg.type == wxpy.TEXT:
        content = from_user + " said" + place + ": " + filter_text(msg.text)
        slack_client.send_message(to_channel, content)
    elif msg.type in [wxpy.PICTURE, wxpy.VIDEO, wxpy.ATTACHMENT, wxpy.RECORDING]:
        filepath = "temp/" + msg.file_name
        data = msg.get_file(filepath)
        comment = from_user + " sent a " + msg.type + place + ": " + msg.file_name
        slack_client.upload_file(to_channel, msg.file_name, filepath, comment)
    else:
        pass


def handle_direct_message(msg: wxpy.Message):
    if config.botadmin:
        logging.info('direct message: %r', msg.sender.name)
        forward_msg_to_slack(msg, msg.sender.name, config.botadmin)


def handle_friend_request(msg):
    if config.auto_accept:
        new_friend = msg.card.accept()
        new_friend.send("Thanks for adding me.")


def handle_msg_all(msg: wxpy.Message):
    try:
        logging.info("group message: %r %r", msg.sender.name, msg.member.name)
        groupname = html.unescape(msg.sender.name)
        username = msg.member.name
        if groupname in config.wechat_slack_map:
            channelname = config.wechat_slack_map[groupname]
            forward_msg_to_slack(msg, username, channelname)
        if msg.is_at and config.botadmin:
            forward_msg_to_slack(msg, username, config.botadmin, groupname)

    except Exception as e:
        logging.exception(e)


def get_first(found):
    if not isinstance(found, list):
        raise TypeError('expected list, {} found'.format(type(found)))
    elif not found:
        raise ValueError('not found')
    else:
        return found[0]


class WxbotNotCreatedException(Exception): pass


def get_group_by_name(group_name):
    if isinstance(group_name, str):
        if wxbot:
            return get_first(wxbot.groups().search(group_name))
        else:
            raise WxbotNotCreatedException()
    else:
        return group_name


def wxbot_main():
    while True:
        global wxbot
        wxbot = wxpy.Bot(console_qr=True, cache_path=True)
        wxbot.register(wxpy.Friend)(handle_direct_message)
        wxbot.register(msg_types=wxpy.FRIENDS, enabled=config.auto_accept)(handle_friend_request)
        wxbot.register(wxpy.Group)(handle_msg_all)
        wxbot.join()
        time.sleep(60.0)


