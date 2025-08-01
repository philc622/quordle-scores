import imaplib
import argparse
import email
import os
import sqlite3
from getpass import getpass
import emoji
from datetime import datetime

def create_database(quordle_db_name='quordle_scores.db'):
    """Create SQLite database and table if they don't exist"""
    conn = sqlite3.connect(quordle_db_name)
    cursor = conn.cursor()
    
    # Create table to store Quordle scores
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quordle_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email_date TEXT,
        parsed_date TEXT,
        score1 INTEGER,
        score2 INTEGER,
        score3 INTEGER,
        score4 INTEGER,
        raw_email TEXT,
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    return conn, cursor

def read_sent_emails(quordle_db_name ,username=None, password=None, imap_server=None, port=993):
    # Connect to database
    conn, cursor = create_database(quordle_db_name)
    
    if not imap_server:
        imap_server = os.environ.get('IMAP_SERVER')
        if not imap_server:
            imap_server = input("Enter your IMAP server: ")

    if not username:
        username = os.environ.get('EMAIL_USERNAME')
        if not username:
            username = input("Enter your email username: ")

    # If no password is provided, try to get it from environment variable or prompt
    if not password:
        password = os.environ.get('EMAIL_PASSWORD')
        if not password:
            password = getpass(f"Enter password for {username}: ")
    
    # Connect to the IMAP server
    mail = imaplib.IMAP4_SSL(imap_server, port)
    
    try:
        # Login to the account
        mail.login(username, password)
        
        # Try multiple ways of selecting the sent folder
        sent_folder_attempts = [
            '"Inbox"'
        ]
        
        scores_saved = 0
        
        for folder in sent_folder_attempts:
            try:
                # Use raw string and encode to handle potential special characters
                status, messages = mail.select(folder.encode('utf-8'), readonly=True)
                
                if status == 'OK':
                    print(f"Successfully selected {folder} folder")
                    
                    # Use US-ASCII search to avoid potential encoding issues
                    search_type = 'TO'
                    search_criteria = f'TO "{username}"'
                    
                    # Perform the search
                    typ, search_data = mail.search(None, search_criteria.encode('us-ascii'))
                    
                    # Get email IDs
                    email_ids = search_data[0].split()
                    
                    # If no emails found, continue to next folder
                    if not email_ids:
                        print(f"No emails found in {folder} folder to {username}")
                        continue
                    
                    # Limit to first 100 emails
                    emails_to_read = email_ids[:100]
                    
                    # Store emails to process after closing connection
                    email_contents = []
                    
                    for email_id in emails_to_read:
                        # Fetch the email message by ID
                        _, msg_data = mail.fetch(email_id, '(RFC822)')
                        
                        # Parse the raw email message
                        for response_part in msg_data:
                            if isinstance(response_part, tuple):
                                msg = email.message_from_bytes(response_part[1])
                                
                                # Extract email content
                                email_info = {
                                    'subject': msg['subject'] or 'No Subject',
                                    'to': msg['to'] or 'Unknown Recipient',
                                    'date': msg['date'] or 'No Date',
                                    'body': ''
                                }
                                
                                # Handle multipart emails
                                if msg.is_multipart():
                                    for part in msg.walk():
                                        if part.get_content_type() == 'text/plain':
                                            try:
                                                email_info['body'] = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                                break
                                            except Exception as decode_error:
                                                print(f"Decoding error: {decode_error}")
                                else:
                                    try:
                                        email_info['body'] = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                                    except Exception as decode_error:
                                        print(f"Decoding error: {decode_error}")
                                
                                email_contents.append(email_info)
                    
                    # Process emails and save to database
                    if email_contents:
                        for email_info in email_contents:
                            scores = parseSnippet(email_info['body'])
                            
                            # Only save valid scores to database
                            if isinstance(scores, list) and len(scores) == 4:
                                # Parse the email date
                                try:
                                    email_date = email_info['date']
                                    # Try to parse the date into a standard format
                                    parsed_date = None
                                    try:
                                        # Parse the email date string into a datetime object
                                        date_obj = email.utils.parsedate_to_datetime(email_date)
                                        # Format as ISO date string
                                        parsed_date = date_obj.strftime('%Y-%m-%d')
                                    except:
                                        parsed_date = None
                                    
                                    # Check if this email's scores are already in the database
                                    cursor.execute('''
                                    SELECT id FROM quordle_scores 
                                    WHERE email_date = ? AND score1 = ? AND score2 = ? AND score3 = ? AND score4 = ?
                                    ''', (email_date, scores[0], scores[1], scores[2], scores[3]))
                                    
                                    existing_record = cursor.fetchone()
                                    
                                    if not existing_record:
                                        # Insert scores into database
                                        cursor.execute('''
                                        INSERT INTO quordle_scores 
                                        (email_date, parsed_date, score1, score2, score3, score4, raw_email) 
                                        VALUES (?, ?, ?, ?, ?, ?, ?)
                                        ''', (email_date, parsed_date, scores[0], scores[1], scores[2], scores[3], email_info['body']))
                                        scores_saved += 1
                                except Exception as db_error:
                                    print(f"Database error: {db_error}")
                        
                        conn.commit()
                        print(f"Saved {scores_saved} new Quordle scores to database")
                        return scores_saved
                
            except Exception as folder_error:
                print(f"Error with folder {folder}: {folder_error}")
                continue
        
        print("Could not find a suitable Sent folder")
        return 0
    
    except imaplib.IMAP4.error as e:
        print(f"IMAP Error: {e}")
        return 0
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return 0
    finally:
        # Close database connection
        conn.commit()
        conn.close()
        
        # Attempt to logout without closing
        try:
            mail.logout()
        except:
            pass

def parseSnippet(msg):
    scores = []
    splitMsg = msg.split()
    # check to see if there was any email content to parse
    if splitMsg:
        emojiScore = ''
        if (splitMsg[0] == 'Daily' and splitMsg[1] == 'Quordle'):
            emojiScore = splitMsg[3] + splitMsg[4]
        elif splitMsg[1] == 'Daily' and splitMsg[2] == 'Quordle':
            emojiScore = splitMsg[4] + splitMsg[5]
        for ii in emojiScore:
            num = ii
            if num.isnumeric():
                scores.append(int(num))  # Convert to integer for database storage
            elif emoji.demojize(num) == ':red_square:':
                scores.append(13)
        if emojiScore:
            return scores
        else:
            print('Email didn\'t start with Quordle and is not being read further')
            return -1
    else:
        print('Email had no parseable content?')
        return -1

def display_scores(quordle_db_name='quordle_scores.db'):
    """Display scores from the database"""
    conn = sqlite3.connect(quordle_db_name)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT parsed_date, score1, score2, score3, score4,(score1+score2+score3+score4), max(score1,score2,score3,score4)
    FROM quordle_scores
    ORDER BY parsed_date DESC
    LIMIT 100
    ''')
    
    scores = cursor.fetchall()
    
    if scores:
        print("\nRecent Quordle Scores:")
        print("-" * 40)
        print("Date       | Score 1 | Score 2 | Score 3 | Score 4 | Sum | Max")
        print("-" * 40)
        for score in scores:
            date, s1, s2, s3, s4, total, max_score = score
            date_str = date if date else "Unknown"
            print(f"{date_str:10} | {s1:7d} | {s2:7d} | {s3:7d} | {s4:7d} | {total:7d} | {max_score:7d}")
    else:
        print("No scores found in database")
        
    conn.close()

# Usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Quorle scores from sent emails and store them in a SQLite database.')

    parser.add_argument('quordledb', help='Path to the SQL database file')
    
    args = parser.parse_args()
    quordle_db_name = args.quordledb
    
    print(f"Using SQL database: {quordle_db_name}")

    emails_processed = read_sent_emails(quordle_db_name)
    
    # Display the scores stored in the database
    if emails_processed > 0:
        print(f"Processed {emails_processed} emails")
    
    display_scores(quordle_db_name)


