#!/usr/bin/env python3
"""Setup Brevo email configuration"""

import getpass
import sys
from pathlib import Path

print("Brevo Email Setup")
print("=" * 50)
print("\nYour SMTP settings:")
print("- SMTP Server: smtp-relay.brevo.com")
print("- Port: 587")
print("- Login: 93b634001@smtp-brevo.com")
print("\nYou need to get your SMTP password from:")
print("https://app.brevo.com/settings/keys/smtp")
print("\nIMPORTANT: This is NOT the API key, it's the SMTP password!")
print("=" * 50)

# Check if .env exists
env_file = Path(".env")
if not env_file.exists():
    print(f"\n❌ Error: {env_file} not found. Run this from the backend directory.")
    sys.exit(1)

# Ask for SMTP password
print("\nEnter your Brevo SMTP password (hidden for security):")
smtp_password = getpass.getpass("SMTP Password: ")

if not smtp_password:
    print("❌ No password entered. Exiting.")
    sys.exit(1)

# Read current .env
with env_file.open() as f:
    lines = f.readlines()

# Update or add BREVO_API_KEY
key_found = False
new_lines = []
for line in lines:
    if line.strip().startswith("BREVO_API_KEY=") or line.strip().startswith(
        "# BREVO_API_KEY="
    ):
        new_lines.append(f"BREVO_API_KEY={smtp_password}\n")
        key_found = True
    else:
        new_lines.append(line)

# If key wasn't found, add it after BREVO_SMTP_LOGIN
if not key_found:
    final_lines = []
    for line in new_lines:
        final_lines.append(line)
        if line.strip().startswith("BREVO_SMTP_LOGIN="):
            final_lines.append(f"BREVO_API_KEY={smtp_password}\n")
            key_found = True
    new_lines = final_lines

# Write back to .env
with env_file.open("w") as f:
    f.writelines(new_lines)

print("\n✅ SMTP password has been set in .env")

# Ask if they want to disable dev mode
response = input(
    "\nDo you want to disable email dev mode and send real emails? (y/N): "
)
if response.lower() == "y":
    # Update EMAIL_DEV_MODE
    with env_file.open() as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.strip().startswith("EMAIL_DEV_MODE="):
            new_lines.append("EMAIL_DEV_MODE=false\n")
        else:
            new_lines.append(line)

    with env_file.open("w") as f:
        f.writelines(new_lines)

    print("✅ Email dev mode disabled. Emails will now be sent via Brevo.")
else:
    print("INFO: Email dev mode remains enabled. Emails will be logged to console.")

print("\n✅ Email setup complete!")
print("\nTo test your email configuration, run:")
print("  python debug_email.py")
