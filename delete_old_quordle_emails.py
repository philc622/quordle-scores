import imaplib
import argparse
import email
import os
from getpass import getpass
from datetime import datetime, timedelta

def is_quordle_email(msg_body):
    """
    Checks if the email body content is a Quordle score email.
    Based on the logic in email-reader-with-sqlite.py's parseSnippet function.
    """
    if not msg_body:
        return False

    splitMsg = msg_body.split()
    if splitMsg:
        if (len(splitMsg) >= 2 and splitMsg[0] == 'Daily' and splitMsg[1] == 'Quordle'):
            return True
        elif (len(splitMsg) >= 3 and splitMsg[1] == 'Daily' and splitMsg[2] == 'Quordle'):
            return True
    return False

def delete_old_quordle_emails(username=None, password=None, imap_server=None, port=993, dry_run=True, days=30):
    if not imap_server:
        imap_server = os.environ.get('IMAP_SERVER')
        if not imap_server:
            imap_server = input("Enter your IMAP server: ")

    if not username:
        username = os.environ.get('EMAIL_USERNAME')
        if not username:
            username = input("Enter your email username: ")

    if not password:
        password = os.environ.get('EMAIL_PASSWORD')
        if not password:
            password = getpass(f"Enter password for {username}: ")

    # Connect to the IMAP server
    mail = imaplib.IMAP4_SSL(imap_server, port)

    try:
        # Login to the account
        mail.login(username, password)

        # Select Inbox
        status, _ = mail.select('"Inbox"', readonly=False)
        if status != 'OK':
            print("Failed to select Inbox")
            return

        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days)
        # Format for IMAP: DD-Mon-YYYY
        imap_date = cutoff_date.strftime("%d-%b-%Y")

        print(f"Searching for Quordle emails older than {days} days (before {imap_date})...")

        # Search for emails BEFORE the cutoff date containing "Quordle"
        # This is more efficient than fetching all old emails
        search_criteria = f'(BEFORE {imap_date} TEXT "Quordle")'
        typ, search_data = mail.search(None, search_criteria)

        if typ != 'OK':
            print(f"Search failed with status: {typ}")
            return

        email_ids = search_data[0].split()
        if not email_ids:
            print("No old emails found.")
            return

        print(f"Found {len(email_ids)} emails older than {days} days. Filtering for Quordle scores...")

        deleted_count = 0

        for email_id in email_ids:
            # Fetch the email headers and body
            _, msg_data = mail.fetch(email_id, '(RFC822)')

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = msg['subject'] or 'No Subject'
                    date_str = msg['date'] or 'No Date'

                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == 'text/plain':
                                try:
                                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                    break
                                except:
                                    pass
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                        except:
                            pass

                    if is_quordle_email(body) or "Quordle" in subject:
                        if dry_run:
                            print(f"[DRY-RUN] Would delete: {subject} (Date: {date_str})")
                        else:
                            print(f"Deleting: {subject} (Date: {date_str})")
                            mail.store(email_id, '+FLAGS', '\\Deleted')
                            deleted_count += 1

        if not dry_run and deleted_count > 0:
            mail.expunge()
            print(f"Successfully deleted {deleted_count} emails.")
        elif dry_run:
            print("Dry run completed. No emails were deleted.")
        else:
            print("No Quordle emails found to delete.")

    except imaplib.IMAP4.error as e:
        print(f"IMAP Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        try:
            mail.logout()
        except:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Delete Quordle score emails older than a specified number of days.')
    parser.add_argument('--days', type=int, default=30, help='Number of days (default: 30)')
    parser.add_argument('--dry-run', action='store_true', dest='dry_run', help='Perform a dry run (default: True)')
    parser.add_argument('--no-dry-run', action='store_false', dest='dry_run', help='Perform actual deletion')
    parser.set_defaults(dry_run=True)

    args = parser.parse_args()

    delete_old_quordle_emails(dry_run=args.dry_run, days=args.days)
