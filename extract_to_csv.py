import argparse
import sqlite3
import csv
from pathlib import Path

def export_scores_to_csv(quordle_db_name='quordle_scores.db', output_filename='quordle_scores.csv'):
    """
    Query the quordle_scores database and export to a CSV file with columns:
    date, score1, score2, score3, score4, sum, max
    
    Args:
        output_filename (str): Name of the output CSV file
    
    Returns:
        str: Path to the created CSV file or error message
    """
    try:
        # Connect to the database
        conn = sqlite3.connect(quordle_db_name)
        cursor = conn.cursor()
        
        # Query only the raw scores and date
        cursor.execute('''
        SELECT 
            parsed_date,
            score1, 
            score2, 
            score3, 
            score4
        FROM quordle_scores
        ORDER BY parsed_date DESC
        ''')
        
        # Fetch all rows
        scores = cursor.fetchall()
        
        if not scores:
            return "No scores found in the database"
        
        # Write to CSV with calculated columns
        with open(output_filename, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            
            # Write header with date as first column
            csv_writer.writerow(['Date', 'Score 1', 'Score 2', 'Score 3', 'Score 4', 'Sum', 'Max'])
            
            # Write data rows with calculated columns
            for row in scores:
                date, score1, score2, score3, score4 = row
                
                # Calculate sum and max in Python
                score_sum = score1 + score2 + score3 + score4
                score_max = max(score1, score2, score3, score4)
                
                # Write row with date first, followed by scores and calculations
                csv_writer.writerow([date, score1, score2, score3, score4, score_sum, score_max])
        
        # Close connection
        conn.close()
        
        # Get absolute path to the file
        file_path = Path(output_filename).absolute()
        
        return f"Successfully exported {len(scores)} records to {file_path}"
    
    except sqlite3.Error as e:
        return f"Database error: {e}"
    except Exception as e:
        return f"Error exporting data: {e}"

# Example usage (if run as standalone script)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extracts Quordle scores from a SQL database and exports them to a CSV file.')

    parser.add_argument('quordledb', help='Path to the SQL database file')
    parser.add_argument('outputcsv', help='Path to the generated CSV file')
    
    args = parser.parse_args()
    quordle_db_name = args.quordledb
    output_filename = args.outputcsv
    
    print(f"Using SQL database: {quordle_db_name}")

    result = export_scores_to_csv(quordle_db_name, output_filename)
    print(result)