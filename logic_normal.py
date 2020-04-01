# -*- coding: utf-8 -*-
#########################################################
# python
import os
import datetime
import traceback
import urllib
import time
from datetime import datetime
import re
import subprocess

# third-party
from sqlalchemy import desc
from sqlalchemy import or_, and_, func, not_
import requests
from lxml import html
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError, APIC, TT2, TPE1, TRCK, TALB, USLT, error, TIT2, TORY, TCON, TYER, USLT
from mutagen.mp3 import EasyMP3 as MP3
from mutagen.mp4 import MP4
from mutagen.flac import FLAC
import mutagen
import platform




# sjva 공용
from framework import app, db, scheduler, path_app_root, celery
from framework.job import Job
from framework.util import Util


# 패키지
from .plugin import logger, package_name
from .model import ModelSetting, ModelItem

headers = {
    
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding' : 'gzip, deflate, br',
    'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer' : '',
    'Host': 'www.bobaedream.co.kr'
} 


#########################################################
class LogicNormal(object):
    session = requests.Session()
    driver = None
    
    @staticmethod
    @celery.task
    def scheduler_function():
        
        # 자동 추가 목록에 따라 큐에 집어넣음.
        try:
            logger.debug("보배포토 시작!")
            
            download_path = ModelSetting.get('download_path')
            getContentCnt = ModelSetting.get('getContentCnt')
            lastNo = ModelSetting.get('lastNo')
            logger.debug( "download_path : %s", download_path )
            
            url = 'https://www.bobaedream.co.kr/list?code=girl&or_gu=10&or_se=desc&pagescale=%s&type=list' %(getContentCnt)
            url = '%s' % (url)
            
            logger.debug( "url : " + url)

            data = LogicNormal.get_html(url)
            tree = html.fromstring(data)

            maxNo = 0
            
            trs = tree.xpath('/html/body/div[5]/div[2]/div[2]/table/tbody/tr')
            for i in range(len(trs)):
                
                td = tree.xpath('/html/body/div[5]/div[2]/div[2]/table/tbody/tr')[i]
                no = str(td[0].text).strip()
                logger.debug("no : %s", no)

                
                
                if no != "None":

                    aTag = tree.xpath('/html/body/div[5]/div[2]/div[2]/table/tbody/tr[%s]/td[2]/a[1]'%(i+1))[0]
                    logger.debug("aTag : %s", aTag.get('href').strip())
                    pageNo = aTag.get('href').strip()

                    for p in pageNo.split("&"):
                        if p[:2] == "No":
                            pageNo = p[3:]

                    if int( maxNo ) < int(pageNo):
                        maxNo = pageNo
                    if int( lastNo ) >= int( pageNo ):
                        logger.debug("PASS")
                        continue

                    try:
                        from bs4 import BeautifulSoup
                    except:
                        os.system("pip install beautifulsoup4")
                        from bs4 import BeautifulSoup
                    
                    bodyURL = 'https://www.bobaedream.co.kr%s'%(aTag.get('href').strip())
                    bodyData = LogicNormal.get_html(bodyURL)
                    logger.debug( "bodyURL : " + bodyURL)
                    
                    soup = BeautifulSoup(bodyData, 'html.parser')

                    bodyCont = soup.find('div', class_='bodyCont')
                    for img in bodyCont.find_all('img'):
                        logger.debug("img : %s",img['src'])

                        try:
                            LogicNormal.getImage(img['src'])
                        except Exception as e:
                            logger.debug("ERR: %s", img['src'])
                            logger.debug(e)

                        time.sleep(3)
                    #time.sleep(3)

            ModelSetting.set('lastNo', maxNo)
            logger.debug("===============END=================")
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def get_html(url, referer=None, stream=False):
        try:
            data = ""

            if LogicNormal.session is None:
                LogicNormal.session = requests.session()
            #logger.debug('get_html :%s', url)
            headers['Referer'] = '' if referer is None else referer
            try:
                page_content = LogicNormal.session.get(url, headers=headers)
            except Exception as e:
                logger.debug("Connection aborted!!!!!!!!!!!")
                time.sleep(10) #Connection aborted 시 10초 대기 후 다시 시작
                page_content = LogicNormal.session.get(url, headers=headers)

            data = page_content.text
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
        return data
    
    
    @staticmethod
    def getImage(img):

        download_path = ModelSetting.get('download_path')
        created_time = datetime.now().strftime('%Y%m%d') 

        coverFile = ""
        ext = ""
        res = requests.get( img, stream=True)

        dt = datetime.now()
        nowtime = "%s%s%s%s%s%s%s" % ( dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond )
        ext = res.headers['Content-Type'].split("/")[-1].lower()
        
        imageFile = os.path.join(download_path, 'photo', created_time, nowtime+'.'+ext)
        
        if not os.path.isfile(imageFile):
            if not os.path.isdir(os.path.join(download_path, 'photo', created_time)):
                logger.debug("폴더 생성 : " + os.path.join(download_path, 'photo', created_time))
                os.makedirs(os.path.join(download_path, 'photo', created_time))
        
            rtn = subprocess.check_output (['curl', '-o', imageFile, img])
            logger.debug("저장 : %s to %s", img, imageFile)
        


        

    
        
        


        
        
        
        
        
