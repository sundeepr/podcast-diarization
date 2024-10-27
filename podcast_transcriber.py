import sqlite3
from datetime import datetime
import torch
from speechbox import ASRDiarizationPipeline
import json
import os
import threading
import time


device = "cuda:0" if torch.cuda.is_available() else "cpu"
asdr_pipeline = ASRDiarizationPipeline.from_pretrained("openai/whisper-medium", device=torch.device("cuda"))

def transcribe_audio_file(filename):
    print("Transcribing "+filename+".mp3")
    trans_start_time = time.time()
    out = asdr_pipeline("podcasts/"+filename+".mp3",device)
    with open(os.path.join("transcripts/"+filename+"_transcript.json"), "w", encoding="utf-8") as f:
        json.dump(out, f)
    trans_end_time = time.time() -trans_start_time
    hours, rem = divmod(trans_end_time, 3600)
    minutes, seconds = divmod(rem, 60)
    time_formatted = "{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))
    print(f"Finished Transcription in : {time_formatted}")

def display_elapsed_time():
    start_time = time.time()
    try:
        while thread.is_alive():  # Keep showing time while the thread is running
            elapsed_time = time.time() - start_time
            hours, rem = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(rem, 60)
            time_formatted = "{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))
            print(f"Time elapsed: {time_formatted}", end='\r')
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nCtrl+C detected! Stopping the timer...")


# Connect to the SQLite database (podcasts.db)
conn = sqlite3.connect('podcasts.db')
cursor = conn.cursor()

# Query to select rows where published_date is before September 1, 2024
cursor.execute('''
    SELECT title FROM downloaded_podcasts WHERE transcribed = False
''')

# Fetch and print all the results
rows = cursor.fetchall()
print(len(rows))
try:
    if rows:
        for row in rows:
            #print("Transcribing file "+row[0])
            thread = threading.Thread(target=transcribe_audio_file,  args=(row[0],))
            thread.start()

            # Show the elapsed time while the function runs in the background
            display_elapsed_time()

            # Wait for the function to complete
            thread.join()

            print("Transcription success")
            cursor.execute('''
                            UPDATE downloaded_podcasts
                            SET transcribed = 1
                            WHERE title = ?
                            ''',(row[0],))
            conn.commit()
            #print(row[0])
    else:
        print("No podcasts found to be transcribed")
except Exception as e:
    print(f"An error occurred: {e}")
    print("\nCtrl+C detected! Exiting program.")
# Close the connection
conn.close()
