#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import collections
import hashlib
import logging
import math
import argparse
import getpass
import time
import requests


session = requests.session()

session.headers.update({
    'User-Agent': 'iOS_HaiJia;v5.2.1; (iPhone; iOS_haijia 14.7.1; Scale/2.00;2001044)',
})


def login(username, passwd):
    logging.info(f'Login {username}...')
    passwd_md5 = hashlib.md5(passwd.encode()).hexdigest()
    resp = session.post('http://api.xuechebu.com/usercenter/userinfo/login',
                        data={
                            'passwordmd5': passwd_md5,
                            'username': username,
                        }).json()
    assert resp['code'] == 0, resp.get('message', 'Unknown')
    name = resp['data']['XM']
    loc = resp['data']['JXMC']
    logging.info(f'Login success. {name} @ {loc}')


ChapterInfo = collections.namedtuple('ChapterInfo', ('id', 'name', 'vid'))


def get_next_chapter(class_name):
    logging.info('Getting next chapter info...')
    resp = session.post('http://xuexiapi.xuechebu.com/videoApiNew/SpPlay/GetChapterInfo',
                        data={'km': class_name}).json()
    assert resp['code'] == 0, resp.get('message', 'Unknown')
    chapter = ChapterInfo(id=resp['data']['ID'],
                          name=f"{resp['data']['KSMC']}-{resp['data']['ZJMC']}",
                          vid=resp['data']['VID'])
    logging.info(f'Got next chapter info: {chapter}')
    return chapter



def report_progress(chapter):
    resp = session.get(f'https://player.polyv.net/secure/{chapter.vid}.js').json()
    duration = math.ceil(float(resp['duration']))
    logging.info(f'Chapter duration: {duration}')

    resp = session.post('http://xuexiapi.xuechebu.com/videoApiNew/SpPlay/SetPlayProgress',
                        data={
                            'Id': chapter.id,
                            'Type': '4',
                            'beforeWatchTime': 0,
                            'thisWatchLocation': duration-1,
                            'thisWatchTime': duration,
                        }).json()
    assert resp['code'] == 0, resp.get('message', 'Unknown')
    logging.info(f'Report progress for {chapter} done!')



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('username')
    parser.add_argument('-c', '--class_name', default='1', help='Which class (1 or 4) are you taking')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    passwd = getpass.getpass()
    login(args.username, passwd)

    last_chapter = None
    while True:
        chapter = get_next_chapter(args.class_name)
        if last_chapter and chapter.id == last_chapter.id:
            logging.error('Already finished, return')
            break
        report_progress(chapter)
        last_chapter = chapter
        time.sleep(1)
