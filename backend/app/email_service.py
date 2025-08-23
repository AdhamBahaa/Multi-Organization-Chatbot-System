"""
Email service for sending setup links and notifications
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@yourcompany.com")
        self.app_name = os.getenv("APP_NAME", "RAG Chatbot System")
        self.app_url = os.getenv("APP_URL", "http://localhost:3000")
        
    def send_setup_email(self, to_email: str, full_name: str, setup_link: str, role: str = "user") -> bool:
        """
        Send password setup email to new admin or user
        
        Args:
            to_email: Recipient email address
            full_name: Recipient's full name
            setup_link: Password setup link
            role: 'admin' or 'user'
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Welcome to {self.app_name} - Set Your Password"
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Email content
            role_title = "Administrator" if role == "admin" else "User"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Welcome to {self.app_name}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                    .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🤖 {self.app_name}</h1>
                        <p>Welcome to your new account!</p>
                    </div>
                    
                    <div class="content">
                        <h2>Hello {full_name}!</h2>
                        
                        <p>Welcome to <strong>{self.app_name}</strong>! Your account has been created successfully as a <strong>{role_title}</strong>.</p>
                        
                        <div class="warning">
                            <strong>⚠️ Important:</strong> To complete your account setup, you need to set your password.
                        </div>
                        
                        <p>Please click the button below to set your password and activate your account:</p>
                        
                        <div style="text-align: center;">
                            <a href="{self.app_url}{setup_link}" class="button">
                                🔐 Set Your Password
                            </a>
                        </div>
                        
                        <p><strong>Or copy this link:</strong><br>
                        <a href="{self.app_url}{setup_link}">{self.app_url}{setup_link}</a></p>
                        
                        <h3>What happens next?</h3>
                        <ol>
                            <li>Click the "Set Your Password" button above</li>
                            <li>Enter a secure password (minimum 6 characters)</li>
                            <li>Confirm your password</li>
                            <li>You'll be redirected to the login page</li>
                            <li>Login with your email and new password</li>
                        </ol>
                        
                        <div class="warning">
                            <strong>🔒 Security Note:</strong> This setup link is unique to your account and should not be shared with others.
                        </div>
                        
                        <p>If you have any questions or need assistance, please contact your system administrator.</p>
                        
                        <p>Best regards,<br>
                        <strong>{self.app_name} Team</strong></p>
                    </div>
                    
                    <div class="footer">
                        <p>This is an automated message from {self.app_name}. Please do not reply to this email.</p>
                        <p>If you didn't expect this email, please contact your administrator.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_content = f"""
            Welcome to {self.app_name}!
            
            Hello {full_name}!
            
            Welcome to {self.app_name}! Your account has been created successfully as a {role_title}.
            
            IMPORTANT: To complete your account setup, you need to set your password.
            
            Please visit this link to set your password:
            {self.app_url}{setup_link}
            
            What happens next?
            1. Click the link above
            2. Enter a secure password (minimum 6 characters)
            3. Confirm your password
            4. You'll be redirected to the login page
            5. Login with your email and new password
            
            SECURITY NOTE: This setup link is unique to your account and should not be shared with others.
            
            If you have any questions, please contact your system administrator.
            
            Best regards,
            {self.app_name} Team
            
            ---
            This is an automated message from {self.app_name}. Please do not reply to this email.
            """
            
            # Attach both versions
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Setup email sent successfully to {to_email}")
            return True
        
        except Exception as e:
            print(f"❌ Failed to send setup email to {to_email}: {e}")
            return False

    def send_password_change_notification(self, to_email: str, full_name: str, role: str = "user") -> bool:
        """
        Send password change notification email
        
        Args:
            to_email: Recipient email address
            full_name: Recipient's full name
            role: 'admin' or 'user'
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Password Changed - {self.app_name}"
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Email content
            role_title = "Administrator" if role in ["admin", "super_admin"] else "User"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Password Changed - {self.app_name}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                    .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin: 20px 0; }}
                    .success {{ background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 8px; margin: 20px 0; color: #155724; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔐 Password Changed</h1>
                        <p>Your password has been updated successfully</p>
                    </div>
                    
                    <div class="content">
                        <h2>Hello {full_name}!</h2>
                        
                        <div class="success">
                            <strong>✅ Success:</strong> Your password for <strong>{self.app_name}</strong> has been changed successfully.
                        </div>
                        
                        <p>This notification is sent to confirm that your password was updated at your request.</p>
                        
                        <div class="warning">
                            <strong>🔒 Security Reminder:</strong>
                            <ul>
                                <li>Keep your new password secure and don't share it with anyone</li>
                                <li>If you didn't request this password change, please contact your system administrator immediately</li>
                                <li>Consider using a strong, unique password</li>
                            </ul>
                        </div>
                        
                        <h3>Account Details:</h3>
                        <ul>
                            <li><strong>Email:</strong> {to_email}</li>
                            <li><strong>Role:</strong> {role_title}</li>
                            <li><strong>Action:</strong> Password Change</li>
                        </ul>
                        
                        <p>If you have any questions or need assistance, please contact your system administrator.</p>
                        
                        <p>Thank you for using {self.app_name}!</p>
                    </div>
                    
                    <div class="footer">
                        <p>This is an automated message from {self.app_name}</p>
                        <p>Please do not reply to this email</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_content = f"""
            Password Changed - {self.app_name}
            
            Hello {full_name}!
            
            Your password for {self.app_name} has been changed successfully.
            
            This notification is sent to confirm that your password was updated at your request.
            
            Security Reminder:
            - Keep your new password secure and don't share it with anyone
            - If you didn't request this password change, please contact your system administrator immediately
            - Consider using a strong, unique password
            
            Account Details:
            - Email: {to_email}
            - Role: {role_title}
            - Action: Password Change
            
            If you have any questions or need assistance, please contact your system administrator.
            
            Thank you for using {self.app_name}!
            
            This is an automated message from {self.app_name}
            Please do not reply to this email
            """
            
            # Attach both versions
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Password change notification sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send password change notification to {to_email}: {e}")
            return False
    
    def send_welcome_email(self, to_email: str, full_name: str, role: str = "user") -> bool:
        """
        Send welcome email after password is set
        
        Args:
            to_email: Recipient email address
            full_name: Recipient's full name
            role: 'admin' or 'user'
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Welcome to {self.app_name} - Account Activated!"
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            role_title = "Administrator" if role == "admin" else "User"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Account Activated - {self.app_name}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>✅ Account Activated!</h1>
                        <p>Welcome to {self.app_name}</p>
                    </div>
                    
                    <div class="content">
                        <h2>Hello {full_name}!</h2>
                        
                        <p>🎉 Congratulations! Your account has been successfully activated as a <strong>{role_title}</strong>.</p>
                        
                        <p>You can now access your account and start using {self.app_name}.</p>
                        
                        <div style="text-align: center;">
                            <a href="{self.app_url}/login" class="button">
                                🚀 Access Your Account
                            </a>
                        </div>
                        
                        <h3>What you can do now:</h3>
                        <ul>
                            <li>Login to your dashboard</li>
                            <li>Explore the system features</li>
                            <li>Manage your profile</li>
                            <li>Access your organization's resources</li>
                        </ul>
                        
                        <p>If you have any questions or need assistance, please contact your system administrator.</p>
                        
                        <p>Best regards,<br>
                        <strong>{self.app_name} Team</strong></p>
                    </div>
                    
                    <div class="footer">
                        <p>This is an automated message from {self.app_name}. Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Account Activated - {self.app_name}
            
            Hello {full_name}!
            
            🎉 Congratulations! Your account has been successfully activated as a {role_title}.
            
            You can now access your account and start using {self.app_name}.
            
            Login here: {self.app_url}/login
            
            What you can do now:
            - Login to your dashboard
            - Explore the system features
            - Manage your profile
            - Access your organization's resources
            
            If you have any questions, please contact your system administrator.
            
            Best regards,
            {self.app_name} Team
            
            ---
            This is an automated message from {self.app_name}. Please do not reply to this email.
            """
            
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Welcome email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send welcome email to {to_email}: {e}")
            return False

# Global email service instance
email_service = EmailService()
