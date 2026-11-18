"""
邮件发送模块 - 发送通知邮件到 leon2019@yahoo.com.hk
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import json



def send_email(to_email='leontang2010@gmail.com', subject='', content=''):
    """
    发送邮件到 leon20191@yahoo.com.hk
    
    Args:
        subject: 邮件主题
        content: 邮件内容（纯文本）
    
    Returns:
        bool: 是否发送成功
    """
    # 邮箱配置
    from_email = '904050606@qq.com'
    from_password = 'niegtnwfwgagbeac'
    # to_email = 'leontang2010@gmail.com'
    # to_email = to_email
    smtp_server = 'smtp.qq.com'
    smtp_port = 465
    from_name = '抢购通知'
    
    try:
        # 构建邮件
        msg = MIMEMultipart()
        msg['From'] = formataddr((from_name, from_email))
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(content, 'plain', 'utf-8'))
        
        # 发送
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(from_email, from_password)
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        
        print(f"✅ 邮件发送成功: {subject}")
        return True
        
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False

json_data = {
    "subject": "测试邮件",
    "content": "这是一封测试邮件"
}
# # ok_content转换为字符串
# ok_content_str = json.dumps(json_data, ensure_ascii=False, indent=2)
# # 发送订购成功邮件通知
# send_email(to_email='k2049@qq.com', subject="抢购成功通知", content=ok_content_str)
# send_email(to_email='leontang2010@gmail.com', subject="抢购成功通知", content=ok_content_str)
