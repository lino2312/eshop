"""
邮件发送模块 - 发送抢购成功通知
"""
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

NOTIFY_EMAILS = [
    "k2049@qq.com",
    "leontang2010@gmail.com",
    "jimmy1231cwec@gmail.com",
    "felix8889990001111@gmail.com",
]

FROM_EMAIL = "904050606@qq.com"
FROM_PASSWORD = "niegtnwfwgagbeac"
FROM_NAME = "抢购通知"
SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 465


def _build_message(to_email, subject, content):
    msg = MIMEMultipart()
    msg["From"] = formataddr((FROM_NAME, FROM_EMAIL))
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(content, "plain", "utf-8"))
    return msg


def _close_quietly(server):
    """信已经交给服务器之后，关闭连接失败不能当成发送失败，否则会再发一封。"""
    try:
        server.quit()
    except Exception:
        try:
            server.close()
        except Exception:
            pass


class MailAccepted(Exception):
    """信很可能已经被服务器收下了（常见于 QQ 发完后立刻断开），不能再重发。"""


def _looks_like_accepted_disconnect(exc):
    if isinstance(exc, smtplib.SMTPServerDisconnected):
        return True
    msg = str(exc).lower()
    return "connection unexpectedly closed" in msg or "please run connect()" in msg


def _send_once(to_email, subject, content):
    """
    单次发送，写法与最初版本一致：SMTP_SSL 465 -> login -> sendmail -> quit。
    不传 context（和最初版本一样不校验证书），所以不依赖对方电脑上有没有根证书。
    """
    msg = _build_message(to_email, subject, content)
    server = None
    step = "连接"
    try:
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30)
        step = "登录"
        server.login(FROM_EMAIL, FROM_PASSWORD)
        step = "发信"
        server.sendmail(FROM_EMAIL, [to_email], msg.as_string())
        step = "关闭"
        _close_quietly(server)
        return True
    except Exception as e:
        if server is not None:
            _close_quietly(server)
        if step in ("发信", "关闭") and _looks_like_accepted_disconnect(e):
            raise MailAccepted(f"{step}时连接断开（邮件可能已发出，不再重试）: {e}") from e
        raise


def send_email(to_email="leontang2010@gmail.com", subject="", content="", retries=8, retry_delay=2):
    """
    发送一封邮件。失败后重试，默认最多试 8 次。
    Returns:
        bool: 是否最终发送成功
    """
    for attempt in range(1, retries + 1):
        try:
            _send_once(to_email, subject, content)
            print(f"✅ 邮件发送成功 -> {to_email}: {subject}")
            return True
        except MailAccepted as e:
            print(f"✅ 邮件按已发送处理 -> {to_email}: {e}")
            return True
        except Exception as e:
            print(f"❌ 邮件发送失败({attempt}/{retries}) -> {to_email}: {e}")
            if attempt < retries:
                time.sleep(retry_delay * attempt)
    return False


def send_success_emails(subject, content, emails=None, rounds=5):
    """
    向所有通知邮箱发送。某一封失败会在后续轮次继续补发，直到全部成功或轮次用尽。
    Returns:
        bool: 是否全部发送成功
    """
    pending = list(emails or NOTIFY_EMAILS)
    for round_no in range(1, rounds + 1):
        if not pending:
            break
        print(f"📧 通知邮件第 {round_no}/{rounds} 轮，待发送: {pending}")
        still_failed = []
        for addr in pending:
            if not send_email(to_email=addr, subject=subject, content=content):
                still_failed.append(addr)
            time.sleep(0.5)
        pending = still_failed
        if pending and round_no < rounds:
            time.sleep(3)

    if pending:
        print(f"❌ 以下邮箱最终仍未发送成功: {pending}")
        return False
    print("✅ 全部通知邮件发送成功")
    return True
