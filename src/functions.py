#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import os
import sys
import urllib
from workflow import Workflow3
from workflow.notify import notify
import requests
import hashlib
import cookielib

reload(sys)
sys.setdefaultencoding('utf8')

COOKIE_FILENAME = 'YoudaoCookie'

LOGIN_URL = 'https://logindict.youdao.com/login/acc/login'
ADD_WORD_URL = 'http://dict.youdao.com/wordbook/wordlist?action=add'
ADD_WORD_TARGET = 'http://dict.youdao.com/wordbook/wordlist'

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 \
(KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'


class VocabularyBook(object):
    '''
    添加单词到单词本，查看单词本，删除单词
    '''

    def __init__(self, username, password, login_url=LOGIN_URL, add_word_url=ADD_WORD_URL):
        self.login_url = login_url
        self.add_word_url = add_word_url

        self.username = username
        self.password = password

        self.res_of_login = None
        self.res_of_addWord = None

        self.cj = cookielib.LWPCookieJar(COOKIE_FILENAME)
        self.conn = requests.Session()
        if os.access(COOKIE_FILENAME, os.F_OK):
            self.cj.load(COOKIE_FILENAME, ignore_discard=True, ignore_expires=True)
            cookie_dict = requests.utils.dict_from_cookiejar(self.cj)
            self.conn.cookies = requests.utils.cookiejar_from_dict(cookie_dict)

        self.header = {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'User-Agent': USER_AGENT
        }

    def loginYoudao(self):
        self.cj.clear()
        self.conn.cookies.clear()
        data = urllib.urlencode(
            {
                'app': 'web',
                'tp': 'urstoken',
                'cf': '3',
                'fr': '1',
                'ru': 'http://dict.youdao.com/wordbook/wordlist?keyfrom=null',
                'product': 'DICT',
                'type': '1',
                'um': 'true',
                'username': self.username,
                'password': hashlib.md5(self.password).hexdigest(),
                'savelogin': '1',

            }
        )
        self.res_of_login = self.conn.post(self.login_url, headers=self.header, data=data, allow_redirects=False)

        if self.res_of_login.headers.get('Set-Cookie').find(self.username) > -1:
            cookie_dict = requests.utils.dict_from_cookiejar(self.conn.cookies)
            requests.utils.cookiejar_from_dict(cookie_dict, self.cj)
            self.cj.save(COOKIE_FILENAME, ignore_discard=True, ignore_expires=True)
            return True
        else:
            return False

    def _add_word(self, word, soundmark='', explains=''):
        self.header.update(
            {
                'Referer': 'http://dict.youdao.com/wordbook/wordlist',
            }
        )

        data = urllib.urlencode(
            {
                'word': word,
                'phonetic': soundmark,
                'desc': explains,
                'tags': 'from Alfred'
            }
        )

        self.res_of_addWord = self.conn.post(self.add_word_url, headers=self.header, data=data, allow_redirects=False)

        if self.res_of_addWord.headers.get('Location') == ADD_WORD_TARGET:
            return True
        else:
            return False

    def add_word(self, word, soundmark, explains):
        if self._add_word(word, soundmark, explains) or \
                (self.loginYoudao() and self._add_word(word, soundmark, explains)):
            notify(u'已经保存至有道单词本', sound='Glass')  #####
        else:
            notify(u'请网络条件好时再次尝试', sound=None)

    def _del_word(self, word):
        pass

    def del_word(self, word):
        pass

    def _show_words(self):
        pass

    def show_words(self):
        return


def main(wf):
    query = wf.args[0]
    job_num = int(wf.args[1])
    translate_info = wf.cached_data('translate_info')
    query = translate_info[0]

    if job_num == 1:
        command = "say --voice='Samantha' " + query
        os.system(command)
    elif job_num == 2:
        uname = os.getenv('USER_NAME', '').strip()
        password = os.getenv('PASSWORD', '').strip()

        if uname and password:
            vb = VocabularyBook(uname, password)
            vb.add_word(query, translate_info[1], ' '.join(translate_info[2]))
        else:
            notify(u'用户名或密码未添加', sound=None)


if __name__ == '__main__':
    wf = Workflow3()
    sys.exit(wf.run(main))
