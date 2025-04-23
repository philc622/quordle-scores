import sqlite3
import csv
from pathlib import Path

def import_scores_from_csv(input_filename='import.csv'):
    scores_saved = 0
    try:
        conn = sqlite3.connect('quordle_scores.db')
        cursor = conn.cursor()

        with open(input_filename, 'r', newline='') as csvfile:
            csv_reader = csv.reader(csvfile)

            csv_reader.__next__()  # Skip header row
            for row in csv_reader:
                # Assuming the CSV has the same structure as the database
                parsed_date = row[0]
                score1 = int(row[1])
                score2 = int(row[2])
                score3 = int(row[3])
                score4 = int(row[4])
                
                # Check if this email's scores are already in the database
                cursor.execute('''
                SELECT id FROM quordle_scores 
                WHERE parsed_date = ? AND score1 = ? AND score2 = ? AND score3 = ? AND score4 = ?
                ''', (parsed_date, score1, score2, score3, score4))
                
                existing_record = cursor.fetchone()
                
                if not existing_record:
                    # Insert scores into database
                    cursor.execute('''
                    INSERT INTO quordle_scores 
                    (parsed_date, score1, score2, score3, score4) 
                    VALUES (?, ?, ?, ?, ?)
                    ''', (parsed_date, score1, score2, score3, score4))
                    scores_saved += 1

               
            
        # Close connection
        conn.commit()
        conn.close()
        
        return f"Successfully imported {scores_saved} records"
    
    except sqlite3.Error as e:
        return f"Database error: {e}"
    except Exception as e:
        return f"Error importing data: {e}"

# Example usage (if run as standalone script)
if __name__ == "__main__":
    result = import_scores_from_csv()
    print(result)