##-*-coding: utf-8;-*-##

import re

def replaceMoreSpace(s):
    return re.sub(r"\s{2,}"," ",s.strip())

def replaceSpace(s):
    return re.sub(r"\s","",s)

if __name__=="__main__":
    s=" helsodfsdf sdfsdf asdfsadi  ! "
    print replaceSpace(s)
    print replaceMoreSpace(s)