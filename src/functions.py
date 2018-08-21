#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
@author: rouwanzi
"""
import os
import sys
from workflow import Workflow3

reload(sys)
sys.setdefaultencoding('utf8')

def main(wf):
    query = wf.args[0]
    job_num = int(wf.args[1])
    
#    with open('test.log','a') as file:
#        file.write(query + '  ' + job_num +'\n')
    if job_num == 1:
        command = "say --voice='Samantha' "+query
        os.system(command)
    elif job_num == 2:
        pass
    
    

if __name__ == '__main__':
    wf = Workflow3()
    sys.exit(wf.run(main))