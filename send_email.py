#!/usr/bin/env python3
"""
Email Sender - Send BioAI newsletter via Gmail SMTP.

Sends the most recent HTML newsletter file as an email attachment.

Environment Variables Required:
    SMTP_EMAIL: Your Gmail address
    SMTP_PASSWORD: Your Gmail app password (NOT your regular password)
    EMAIL_TO: Recipient email address

Usage:
    # Use defaults from environment variables
    python send_email.py

    # Override recipient via CLI
    python send_email.py --to recipient@example.com

    # Specify a specific file instead of most recent
    python send_email.py --file ai_weekly_20260119.html
"""

import argparse
import os
import smtplib
import sys
from datetime import datetime
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from glob import glob
from pathlib import Path

# Gmail SMTP settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Default output directory (relative to script location)
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def get_env_var(name: str, required: bool = True) -> str | None:
    """Get environment variable with helpful error message."""
    value = os.environ.get(name)
    if required and not value:
        raise ValueError(
            f"{name} environment variable not set. "
            f"Set it with: export {name}='your-value-here'"
        )
    return value


def find_most_recent_html(output_dir: str = DEFAULT_OUTPUT_DIR) -> str | None:
    """Find the most recent HTML file in the output directory."""
    pattern = os.path.join(output_dir, "ai_weekly_*.html")
    files = glob(pattern)

    if not files:
        return None

    # Sort by modification time, most recent first
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]


def send_email(
    smtp_email: str,
    smtp_password: str,
    to_address: str,
    attachment_path: str,
    subject: str | None = None
) -> bool:
    """
    Send email with HTML attachment via Gmail SMTP.

    Args:
        smtp_email: Gmail address to send from
        smtp_password: Gmail app password
        to_address: Recipient
        attachment_path: Path to HTML file to attach
        subject: Email subject (auto-generated if None)

    Returns:
        True if successful, False otherwise
    """
    # Generate subject with date if not provided
    if subject is None:
        date_str = datetime.now().strftime("%B %d, %Y")
        subject = f"BioAI Weekly - {date_str}"

    # Create message
    msg = MIMEMultipart()
    msg["From"] = smtp_email
    msg["To"] = to_address
    msg["Subject"] = subject

    # Email body
    body = f"""Hi,

Please find attached the latest BioAI Weekly newsletter.

This week's edition features the top stories in AI for biology research, including community discussions, trending topics, and key developments from respected sources.

Open the HTML file in your web browser to view the formatted newsletter.

Best regards,
Jacob L. Steenwyk
"""
    msg.attach(MIMEText(body, "plain"))

    # Attach HTML file
    attachment_name = os.path.basename(attachment_path)
    try:
        with open(attachment_path, "rb") as f:
            attachment = MIMEBase("text", "html")
            attachment.set_payload(f.read())
            encoders.encode_base64(attachment)
            attachment.add_header(
                "Content-Disposition",
                f"attachment; filename={attachment_name}"
            )
            msg.attach(attachment)
    except FileNotFoundError:
        print(f"Error: Attachment file not found: {attachment_path}")
        return False
    except IOError as e:
        print(f"Error reading attachment: {e}")
        return False

    # Get file size for display
    file_size_kb = os.path.getsize(attachment_path) / 1024

    # Send email
    try:
        print(f"Connecting to Gmail SMTP server...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            print(f"Authenticating as {smtp_email}...")
            server.login(smtp_email, smtp_password)
            print(f"Sending email...")
            server.sendmail(smtp_email, [to_address], msg.as_string())

        print(f"\n{'='*50}")
        print(f"Email sent successfully!")
        print(f"{'='*50}")
        print(f"  From: {smtp_email}")
        print(f"  To: {to_address}")
        print(f"  Subject: {subject}")
        print(f"  Attachment: {attachment_name} ({file_size_kb:.1f} KB)")
        print(f"{'='*50}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("\nError: Authentication failed.")
        print("Make sure you're using a Gmail App Password, not your regular password.")
        print("To create an App Password:")
        print("  1. Enable 2-Factor Authentication on your Google account")
        print("  2. Go to https://myaccount.google.com/apppasswords")
        print("  3. Generate a new App Password for 'Mail'")
        return False
    except smtplib.SMTPException as e:
        print(f"\nSMTP Error: {e}")
        return False
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Send BioAI newsletter via email",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  SMTP_EMAIL      Your Gmail address
  SMTP_PASSWORD   Your Gmail app password
  EMAIL_TO        Recipient email address

Examples:
  python send_email.py
  python send_email.py --to recipient@example.com
  python send_email.py --file ai_weekly_20260119.html
        """
    )

    parser.add_argument(
        "--to",
        help="Override the recipient (default: EMAIL_TO env var)"
    )
    parser.add_argument(
        "--file",
        help="Specific HTML file to send (default: most recent)"
    )
    parser.add_argument(
        "--subject",
        help="Override email subject"
    )

    args = parser.parse_args()

    # Load credentials from environment
    try:
        smtp_email = get_env_var("SMTP_EMAIL")
        smtp_password = get_env_var("SMTP_PASSWORD")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Get recipient (CLI overrides env var)
    try:
        to_address = args.to or get_env_var("EMAIL_TO")
    except ValueError as e:
        print(f"Error: {e}")
        print("You can also specify recipient with --to flag")
        sys.exit(1)

    # Find file to send
    if args.file:
        attachment_path = args.file
        if not os.path.exists(attachment_path):
            print(f"Error: Specified file not found: {attachment_path}")
            sys.exit(1)
    else:
        attachment_path = find_most_recent_html()
        if not attachment_path:
            print(f"Error: No HTML files found in {DEFAULT_OUTPUT_DIR}")
            print("Run the newsletter generator first to create content")
            sys.exit(1)
        print(f"Found most recent file: {attachment_path}")

    # Send the email
    success = send_email(
        smtp_email=smtp_email,
        smtp_password=smtp_password,
        to_address=to_address,
        attachment_path=attachment_path,
        subject=args.subject
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
