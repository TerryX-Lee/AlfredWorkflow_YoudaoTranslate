#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import urllib
from workflow import web,Workflow3
import random
import hashlib
import os
import sys
import functions
reload(sys)
sys.setdefaultencoding('utf8')

ERROR_CODE = {
        '101':'缺少必填的参数，出现这个情况还可能是et的值和实际加密方式不对应',
        '102':'不支持的语言类型',
        '103':'翻译文本过长',
        '104':'不支持的API类型',
        '105':'不支持的签名类型',
        '106':'不支持的响应类型',
        '107':'不支持的传输加密类型',
        '108':'appKey无效，注册账号，登录后台创建应用和实例并完成绑定，可获得应用ID和密钥等信息，其中应用ID就是appKey（ 注意不是应用密钥）',
        '109':'batchLog格式不正确',
        '110':'无相关服务的有效实例',
        '111':'开发者账号无效',
        '113':'q不能为空',
        '201':'解密失败，可能为DES,BASE64,URLDecode的错误',
        '202':'签名检验失败',
        '203':'访问IP地址不在可访问IP列表',
        '205':'请求的接口与选择的接入方式不一致',
        '301':'辞典查询失败',
        '302':'翻译查询失败',
        '303':'服务端的其它异常',
        '401':'账户已经欠费',
        '411':'访问频率受限,请稍后访问',
        '2005':'ext参数不对',
        '2006':'不支持的voice'
        }

LOG_FILE = 'QueryHistory.log'
ARG_CONNECTOR = u'@@'

ICON_LOGO = 'icon_logo.png'
ICON_ERROR = 'icon_error.png'
ICON_PRONOUNCE = 'icon_pronounce.png'
ICON_TRANSLATION = 'icon_translation.png'
ICON_HISTORY = 'icon_history.png'
ICON_DUANYU = 'icon_duanyu.png'
ICON_FOLDER = 'icon_folder.png'
ICON_TRASH = 'icon_trash.png'
ICON_VB = 'icon_vocabularybook.png'

ZHIYUN_URL = 'https://openapi.youdao.com/api'
DICT_URL = 'http://dict.youdao.com/w/%s/'

ZHIYUN_ID = ''
ZHIYUN_KEY = ''

user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36\
 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'

def add_history_query(query,subtitle,fayin):
    with open(LOG_FILE,'a') as file:
        log = query + '  ' + subtitle + ' ' + fayin + '\n'
        file.write(log)
    

def get_history_query():
    try:
        with open(LOG_FILE,'r') as file:
            for item in file.readlines()[-1:-10:-1]:
                temp = item.split('  ')
                wf.add_item(temp[0],subtitle=temp[1],arg=temp[0]+ARG_CONNECTOR+temp[0],valid=True,icon=ICON_HISTORY)
    except IOError:
        wf.add_item(u'没有历史记录',subtitle=u'加油学英语吧~！',icon=ICON_FOLDER)
        
def del_history_query():
    os.remove(LOG_FILE)
    wf.add_item(u'已清空历史记录',subtitle='多多查询，加油学英语吧~！',icon=ICON_TRASH)

#by zhiyun
def translate_by_zhiyun(query,ZHIYUN_ID,ZHIYUN_KEY):
    '''
    returns:   JSON
    '''
    url = ZHIYUN_URL
    salt = random.randint(0,65535)
    sign = hashlib.md5(ZHIYUN_ID+query+str(salt)+ZHIYUN_KEY).hexdigest()
    
    data = {
            'q':urllib.quote(str(query)),
#            'from':'auto',
#            'to':'auto',
            'appKey':ZHIYUN_ID,
            'sign':str(sign),
            'salt':str(salt)
            }
    res = web.get(url,params=data).json()
    
    return res

def handle_res_from_zhiyun(res,query):
    try:
        basic = res['basic']
        
        translations = []
        for i in res['translation']:
            wf.add_item(i,subtitle=u'单词释义',arg=i+ARG_CONNECTOR+query,valid=True,icon=ICON_TRANSLATION)
        
        fayin = ''
        if 'uk-phonetic' in basic:
            fayin += u'英'+'['+basic['uk-phonetic']+'] '
        if 'us-phonetic' in basic:
            fayin += u'美'+'['+basic['us-phonetic']+'] '
        if fayin:
            wf.add_item(fayin,subtitle=u'Shift + Enter发音',arg=fayin+ARG_CONNECTOR+query,valid=True,icon=ICON_PRONOUNCE)        
    
        for i in basic['explains']:
            translations.append(i)
            wf.add_item(i,subtitle=u'单词释义',arg=i+ARG_CONNECTOR+query,valid=True,icon=ICON_TRANSLATION)
        
        duanyu = res['web']
        for i in duanyu:
            head = i['key']
            tail = i['value']
            item = head + ' ' + ','.join(tail)
            wf.add_item(item,subtitle=u'网络释义',arg=item+ARG_CONNECTOR+query,valid=True,icon=ICON_DUANYU)
    except KeyError:
        wf.add_item(u'有道无法翻译...',subtitle='请尝试其他方法查询',icon=ICON_ERROR)
        return []
    
    return translations,fayin

#by dict
def translate_by_dict(query):
    url = DICT_URL % urllib.quote(str(query))
    data = {
            'Connection': 'keep-alive',
            'Content-Encoding': 'gzip',
            'Content-Language': 'zh-CN',
            'Content-Type': 'text/html; charset=utf-8',
#            'User-Agent':user_agent,
            'Vary': 'Accept-Encoding',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Host': 'dict.youdao.com'
            }
    res = web.get(url,params=data)
    
    return res


def handle_res_from_dict(html,query):
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html)
    block = soup.find('div',class_='trans-container')
    temp = block.find_all('a',class_='search-js')
    translations = []
    fayin = ''
    
    if len(temp) != 0:
        for i in temp:
            translations.append(i.string)
            wf.add_item(i.string,subtitle=u'单词释义',arg=i.string+ARG_CONNECTOR+query,valid=True,icon=ICON_LOGO)
        
    else:
        fayin = soup.find_all('span',class_='pronounce')
        fayin = '  '.join(map(lambda x:x.get_text().replace(' ',''),fayin))
        fayin = fayin.replace('\n','')
        if fayin:
            wf.add_item(fayin,subtitle=u'Shift + Enter发音',arg=fayin+ARG_CONNECTOR+query,valid=True,icon=ICON_PRONOUNCE)        
            
        translations = block.find_all('li')
        translations = map(lambda x:x.string,translations)
        for i in translations:
            wf.add_item(i,subtitle=u'单词释义',arg=i+ARG_CONNECTOR+query,valid=True,icon=ICON_TRANSLATION)
        
        duanyu = soup.find_all('p',class_='wordGroup')
        duanyuitems = set()
        for i in duanyu:
            head = i.find('span',class_='contentTitle')
            tail = head.next_sibling.replace(' ','').replace('\n','').replace('\r','')
            if head.string and tail: 
                item = head.string+' '+tail
                if item not in duanyuitems:
                    duanyuitems.add(item)
                    wf.add_item(item,subtitle=u'短语示例',arg=item+ARG_CONNECTOR+query,valid=True,icon=ICON_DUANYU)
            
    return translations,fayin

#
def translate(query,zhiyun_flag):
    if zhiyun_flag:
        res = translate_by_zhiyun(query,ZHIYUN_ID,ZHIYUN_KEY)
        errorCode = res['errorCode']
        if errorCode != u'0':
            if errorCode in ERROR_CODE:
                wf.add_item(ERROR_CODE[errorCode],subtitle='Error!',icon=ICON_ERROR)
            else:
                wf.add_item(u'发生了未知的错误',subtitle='Error!')
        else:
            translations,fayin = handle_res_from_zhiyun(res,query)
            add_history_query(query,' '.join(translations),fayin)
            cache_translate_info(query,fayin,translations)
    else:
        res = translate_by_dict(query)
        translations,fayin = handle_res_from_dict(res.content,query)
        add_history_query(query,' '.join(translations),fayin)
        cache_translate_info(query,fayin,translations)
        
def get_vocabularybook():
    uname = os.getenv('USER_NAME','').strip()
    password = os.getenv('PASSWORD','').strip()
    
    if uname and password:
        vb = functions.VocabularyBook(uname,password)
        words = vb.show_words()
        if not words:
            wf.add_item(u'生词本为空',icon=ICON_ERROR)
            return
        for i in words:
            item = i[0]+i[1]
            subtitle = i[2]
            wf.add_item(item,subtitle=subtitle,arg='',icon=ICON_VB)
            
    else:
        wf.add_item(u'用户名或密码未添加',icon=ICON_ERROR)

def cache_translate_info(word,fayin,translations):
    wf.cache_data('translate_info',[word,fayin]+[translations])

def main(wf):
    global ZHIYUN_ID,ZHIYUN_KEY
    
    query = wf.args[0].strip()
    
    if not isinstance(query,unicode):
        query = query.decode('utf8')
    
    if query == '*':
        get_history_query()
    elif query == '*clear':
        del_history_query()
    elif query == '*vb':
        get_vocabularybook()
    else:
        
        ZHIYUN_ID = os.getenv('ZHIYUN_ID','').strip()
        ZHIYUN_KEY = os.getenv('ZHIYUN_KEY','').strip()
        
        if ZHIYUN_ID and ZHIYUN_KEY:
            translate(query,1)
        else:
            translate(query,0)
    
    wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow3()
    sys.exit(wf.run(main))
    
    