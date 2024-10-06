import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Example usage
# sender_email    = "your_email@gmail.com"
# sender_password = "your_app_password"  # Use an app password, not your regular password
# recipient_email = "user_email@example.com"
# subject         = "Important Notification"
# body            = "This is an important notification from your application."
# 
# send_email_notification(sender_email, sender_password, recipient_email, subject, body)

def send_email_notification(sender_email, sender_password, recipient_email, subject, body):  # Set up the MIME
    message = MIMEMultipart()
    message['From']    = sender_email
    message['To']      = recipient_email
    message['Subject'] = subject

    # Add body to email
    message.attach(MIMEText(body, 'plain'))
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:  # Create SMTP session
        server.starttls()  # Enable security
        server.login(sender_email, sender_password)
        text = message.as_string()
        server.sendmail(sender_email, recipient_email, text)

    print(f"Email notification sent to {recipient_email}")
