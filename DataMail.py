#coding:utf-8
import threading
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication 

# 默认邮箱配置
mail_server_host = 'smtp.yeah.net'
mail_account = 'pcl_send@yeah.net'
mail_password = 'ZIZRRNBFQYOVVQUK'
mail_device = 'Auto Scan System'

class DataMail(threading.Thread): 
    # def __init__(self, to_addr, mail_text, data_path, group: None = ..., target: Callable[..., object] | None = ..., name: str | None = ..., args: Iterable[Any] = ..., kwargs: Mapping[str, Any] | None = ..., *, daemon: bool | None = ...) -> None:
    #     super().__init__(group, target, name, args, kwargs, daemon=daemon)
    def __init__(self, to_addr, mail_title='default title', mail_text='default text', data_path='') -> None:
        threading.Thread.__init__(self)
        self.mail_title = mail_title
        self.mail_text = mail_text
        self.data_path = data_path
        self.to_addr = to_addr
        
    
    def run(self) -> None:
        msg = MIMEMultipart()
        if (self.data_path != '' and os.path.isfile(self.data_path)): 
            file_size = os.path.getsize(self.data_path)
            if (file_size < 50 * 1024 * 1024): 
                dataApart = MIMEApplication(open(file=self.data_path, mode='rb').read())
                dataApart.add_header('Content-Disposition', 'attachment', filename=os.path.basename(self.data_path))
                msg.attach(dataApart)
            else: 
                self.mail_text = self.mail_text + '\r\n[Data file is too big to be send, please copy from computer directly.]'
        textApart = MIMEText(self.mail_text)
        msg.attach(textApart)
        msg['Subject'] = self.mail_title
        msg['From'] = '{}<{}>'.format(mail_device, mail_account)
        msg['To'] = self.to_addr
        try:
            print('[Sending email]')
            server = smtplib.SMTP(mail_server_host)
            server.login(mail_account,mail_password)
            server.sendmail(mail_account, [self.to_addr], msg.as_string())
            print('[Send email success]')
            server.quit()
        except smtplib.SMTPException as e:
            print('[Send email fialed]',e) #打印错误
    
if __name__ == '__main__':
    # test_mail = DataMail(to_addr='1282984748@qq.com') # 空测试
    test_mail = DataMail(to_addr='1282984748@qq.com', mail_text='test mail', data_path="D:/workspace/ArmScan/Data/xOy_2m_聚焦玻璃_11220926.csv") # 8k文件，成功
    # test_mail = DataMail(to_addr='1282984748@qq.com', mail_text='test mail', data_path="D:/workspace/ArmScan/Data/xOy_2m_聚焦玻璃_11181803.csv") # 40M文件，成功
    # test_mail = DataMail(to_addr='1282984748@qq.com', mail_text='test mail', data_path="D:/workspace/ArmScan/Data/xOy_1o5m_方口28G喇叭_空气_11231000.csv") # 100M文件，失败
    # test_mail = DataMail(to_addr='1282984748@qq.com', mail_text='test mail', data_path='D:/workspace/ArmScan/Data/xOy_1o5m_方口28G喇叭_空气_11221819.csv') # 500M文件，失败
    test_mail.setDaemon(False)
    test_mail.start()
    from time import sleep
    for i in range(5): 
        print("hello ", i)
        sleep(0.1)
    pass