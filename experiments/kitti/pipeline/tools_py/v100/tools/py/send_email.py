import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

# 邮件配置（写死账号密码）
SMTP_SERVER = "smtp.qq.com"          # QQ邮箱 SMTP 服务器
SMTP_PORT = 587                      # TLS 端口
SENDER_EMAIL = "2521065305@qq.com"   # 发件人邮箱
SENDER_PASSWORD = "pffpkiucvsqyecda"   # QQ邮箱需使用“授权码”，不是登录密码！
RECEIVER_EMAIL = "2521065305@qq.com" # 收件人邮箱

# 邮件内容
subject = "系统提示"

def send_email(body):
    # 创建邮件
    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = RECEIVER_EMAIL
    message["Subject"] = Header("系统提示", "utf-8")

    # 添加正文
    message.attach(MIMEText(body, "plain", "utf-8"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
        print("✅ 邮件发送成功！")
    except Exception as e:
        print(f"❌ 邮件发送失败：{e}")
    finally:
        try:
            server.quit()
        except:
            pass

if __name__ == "__main__":
    # 检查是否有传入 body 参数
    if len(sys.argv) != 2:
        print("用法: python3 send_email.py <邮件内容>")
        sys.exit(1)

    email_body = sys.argv[1]
    send_email(email_body)