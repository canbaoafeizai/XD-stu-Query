#coding=utf-8
import requests
import http.cookiejar
import lxml.etree
import hashlib


global loginUrl
loginUrl = 'https://zfw.xidian.edu.cn/'
global manageUrl
manageUrl = 'https://zfw.xidian.edu.cn/home'

# printLogFlag := ['debug', 'none']
global printLogFlag
printLogFlag = 'debug'

# 1 人工识别并在命令行输入
# 2 启用打码平台自动打码
global identifyCaptcha
identifyCaptcha = 2

global postHeaders
postHeaders = {
    'Host': 'zfw.xidian.edu.cn',
    # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
    'Referer': loginUrl,
}


class Chaojiying_Client(object):

    def __init__(self, username, password, soft_id):
        self.username = username
        password =  password.encode('utf8')
        self.password = hashlib.md5(password).hexdigest()
        self.soft_id = soft_id
        self.base_params = {
            'user': self.username,
            'pass2': self.password,
            'softid': self.soft_id,
        }
        self.headers = {
            'Connection': 'Keep-Alive',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)',
        }

    def PostPic(self, im, codetype):
        """
        im: 图片字节
        codetype: 题目类型 参考 http://www.chaojiying.com/price.html
        """
        params = {
            'codetype': codetype,
        }
        params.update(self.base_params)
        files = {'userfile': ('ccc.jpg', im)}
        r = requests.post('http://upload.chaojiying.net/Upload/Processing.php', data=params, files=files, headers=self.headers)
        return r.json()

    def ReportError(self, im_id):
        """
        im_id:报错题目的图片ID
        """
        params = {
            'id': im_id,
        }
        params.update(self.base_params)
        r = requests.post('http://upload.chaojiying.net/Upload/ReportError.php', data=params, headers=self.headers)
        return r.json()
global chaojiyingClient
##调用的超级鹰的api，user,pass,key
chaojiyingClient = Chaojiying_Client('user', 'pass', 'key')


def initiate():
    # 初始化脚本所需要的参数和对象
    # 输入: 无
    # 返回: 无

    global mySession
    mySession = requests.Session()


def requestCookie(username, password):
    # 登录，主要作用为POST数据以获得cookie
    # 输入: 用户名, 密码
    # 返回: 无

    global mySession
    global loginUrl
    # 生产环境中请将以下第1行解除注释
    # 2-5行只用于实验环境中
    loginUrlGetResponseText = mySession.get(loginUrl).text
    # with open('login.html', 'w') as f:
    #     f.write(loginUrlGetResponseText)
    # with open('login.html', 'r') as f:
    #     loginUrlGetResponseText = f.read()
    
    etreeHTML = lxml.etree.HTML(loginUrlGetResponseText)

    csrfToken = getCsrfToken(etreeHTML)
    captcha = getCaptcha(etreeHTML)

    global postHeaders

    postData = {
        '_csrf': csrfToken,
        'LoginForm[username]': username,
        'LoginForm[password]': password,
        'LoginForm[verifyCode]': captcha,
        'login-button': '',
    }

    loginUrlPost = mySession.post(loginUrl, headers=postHeaders, data=postData)


def getCsrfToken(etreeHTML):
    # 获取csrfToken
    # 输入: etreeHTML
    # 返回: csrfToken

    csrfTokenXpath = '/html/head/meta[@name="csrf-token"]/@content'
    csrfTokenList = etreeHTML.xpath(csrfTokenXpath)
    csrfToken = csrfTokenList[0]
    return csrfToken


def getCaptcha(etreeHTML):
    # 获取验证码
    # 输入: etreeHTML
    # 返回: captcha

    global loginUrl
    global mySession
    global identifyCaptcha
    partCaptchaUrlXpath = '//img[@id="loginform-verifycode-image"]/@src'
    partCaptchaUrlList = etreeHTML.xpath(partCaptchaUrlXpath)
    partCaptchaUrl = partCaptchaUrlList[0]
    captchaUrl = loginUrl + partCaptchaUrl
    imageContent = mySession.get(captchaUrl).content
    with open('cap.png', 'wb') as fw:
            fw.write(imageContent)

    if identifyCaptcha == 1:
        captcha = input('请打开验证码图片cap.png并人工输入验证码:')
        printLog('getCaptcha', captcha)
        return captcha
    else:
        global chaojiyingClient
        im = open('cap.png', 'rb').read()
        captcha = chaojiyingClient.PostPic(im, 1902)['pic_str']
        #print(captcha)
        return captcha


# FIX: 获取信息
def getInformation():
    # 获取想要的信息
    # 输入: 无
    # 返回: 信息

    global postHeaders
    global mySession
    # 生产环境中请将以下第1行解除注释
    # 2-5行只用于实验环境中
    manageUrlGetResponseText = mySession.get(manageUrl, headers=postHeaders).text
    if '<h1>Forbidden (#403)</h1>' in manageUrlGetResponseText:
        return '登陆失败，可能是验证码错误，请人工输入'
    # with open('manage.html', 'w') as fw:
    #     fw.write(manageUrlGetResponseText)
    # with open('manage.html', 'r') as fr:
    #     manageUrlGetResponseText = fr.read()
    
  
    etreeHTML = lxml.etree.HTML(manageUrlGetResponseText)
    #col1是套餐ID，选择忽略
    #col1Xpath = '//tr[@data-key<1000]/td[1]/text()'
    #col1 = etreeHTML.xpath(col1Xpath)[0]
    col2Xpath = '//tr[@data-key<1000]/td[2]/text()'
    col2 = etreeHTML.xpath(col2Xpath)[0]
    col3Xpath = '//tr[@data-key<1000]/td[3]/text()'
    col3 = etreeHTML.xpath(col3Xpath)[0]
    return '已用流量:{0}\t剩余流量:{1}'.format(col2, col3)


def printLog(functionName, message):
    # 打印日志
    # 输入: 函数名称, 信息
    # 输出: 无

    global printLogFlag
    if printLogFlag == 'debug':
        print('log - {}\t{}'.format(functionName, message))


def main():
    # 函数入口。由三个主要函数构成。

    initiate()
    #传入学号密码信息
    stu_id='123456789'
    stu_pass='123456789'
    requestCookie(stu_id, stu_pass)
    #获取到流量
    info = getInformation()
    print('ID:{}\t'.format(stu_id),end='')
    print(info)


if __name__ == '__main__':
    main()
