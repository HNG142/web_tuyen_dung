import smtplib # Thư viện để gửi email qua giao thức SMTP
from email.mime.text import MIMEText # Để tạo nội dung email dạng văn bản
from email.mime.multipart import MIMEMultipart # Để tạo email có nhiều phần (ví dụ: văn bản và HTML)
from app.config import settings # Nhập các cài đặt email từ config

async def send_email(to_email: str, subject: str, body: str):
    """Gửi một email đến địa chỉ đã cho."""
    # Kiểm tra xem cấu hình email đã đầy đủ chưa
    if not settings.EMAIL_USERNAME or not settings.EMAIL_PASSWORD or not settings.EMAIL_HOST:
        print("Cấu hình email chưa đầy đủ trong .env. Bỏ qua việc gửi email.")
        return False

    msg = MIMEMultipart()
    msg['From'] = settings.EMAIL_USERNAME # Email gửi đi
    msg['To'] = to_email # Email nhận
    msg['Subject'] = subject # Tiêu đề email
    
    msg.attach(MIMEText(body, 'html')) # Đính kèm nội dung email dưới dạng HTML

    try:
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls()  # Bắt đầu kết nối bảo mật TLS
            server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD) # Đăng nhập vào SMTP server
            server.send_message(msg) # Gửi email
        print(f"Email đã được gửi thành công đến {to_email}")
        return True
    except Exception as e:
        print(f"Không thể gửi email đến {to_email}: {e}")
        return False

async def send_offer_email(candidate_email: str, candidate_name: str, position_name: str):
    """Gửi thư mời làm việc."""
    subject = f"Thư mời làm việc - Vị trí {position_name}"
    body = f"""
    <html>
    <body>
        <p>Kính gửi {candidate_name},</p>
        <p>Chúng tôi rất vui mừng thông báo rằng bạn đã được chọn cho vị trí <strong>{position_name}</strong> tại công ty chúng tôi.</p>
        <p>Chúng tôi rất ấn tượng với hồ sơ và các kỹ năng của bạn trong quá trình phỏng vấn và kiểm tra.</p>
        <p>Vui lòng liên hệ với chúng tôi để thảo luận thêm về các điều khoản và quy trình tiếp theo. Bạn có thể trả lời email này hoặc liên hệ qua số điện thoại [ĐIỀN SỐ ĐIỆN THOẠI CỦA CÔNG TY VÀO ĐÂY].</p>
        <p>Chúng tôi mong muốn được chào đón bạn vào đội ngũ của chúng tôi!</p>
        <p>Trân trọng,</p>
        <p>Đội ngũ Tuyển dụng</p>
        <p>[ĐIỀN TÊN CÔNG TY CỦA BẠN VÀO ĐÂY]</p>
    </body>
    </html>
    """
    await send_email(candidate_email, subject, body)

async def send_onboarding_email(candidate_email: str, candidate_name: str):
    """Gửi email chào mừng/onboarding cơ bản."""
    subject = f"Chào mừng bạn đến với [TÊN CÔNG TY CỦA BẠN]!"
    body = f"""
    <html>
    <body>
        <p>Chào mừng {candidate_name},</p>
        <p>Chúng tôi rất vui mừng chào đón bạn đến với đội ngũ của chúng tôi!</p>
        <p>Email này là để xác nhận việc gia nhập của bạn và cung cấp một số thông tin cơ bản để giúp bạn bắt đầu.</p>
        <p>Chúng tôi sẽ liên hệ với bạn trong thời gian sớm nhất để hướng dẫn các bước tiếp theo của quy trình onboarding.</p>
        <p>Trân trọng,</p>
        <p>Đội ngũ Tuyển dụng</p>
        <p>[TÊN CÔNG TY CỦA BẠN]</p>
    </body>
    </html>
    """
    await send_email(candidate_email, subject, body)