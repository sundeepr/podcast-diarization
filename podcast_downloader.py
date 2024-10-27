import feedparser
import requests
import os
import sqlite3
from tqdm import tqdm
import configparser
from datetime import datetime

# Database setup
def setup_db(db_name="podcasts.db"):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    
    # Create a table if it doesn't exist to store podcast info
    c.execute('''
    CREATE TABLE IF NOT EXISTS downloaded_podcasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        url TEXT UNIQUE,
        published_date TEXT
    )
    ''')
    conn.commit()
    return conn, c

# Check if the episode is already downloaded
def is_episode_downloaded(cursor, episode_url):
    cursor.execute('SELECT 1 FROM downloaded_podcasts WHERE url = ?', (episode_url,))
    return cursor.fetchone() is not None

# Add episode to the database
def mark_episode_as_downloaded(cursor, conn, episode_title, episode_url, published_date):
    cursor.execute('''
    INSERT INTO downloaded_podcasts (title, url, published_date)
    VALUES (?, ?, ?)
    ''', (episode_title, episode_url, published_date))
    conn.commit()

# Download podcast episode with progress bar
def download_episode(episode_title, episode_url, download_dir, db_conn, db_cursor, episode_published):
    # Check if the episode has already been downloaded
    if is_episode_downloaded(db_cursor, episode_url):
        print(f"Episode '{episode_title}' has already been downloaded.")
        return

    # Create download directory if it doesn't exist
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    # Define the download path
    file_name = f"{episode_title}.mp3".replace("/", "_")  # Sanitize file name
    file_path = os.path.join(download_dir, file_name)

    # Download the episode
    response = requests.get(episode_url, stream=True)
    total_size = int(response.headers.get('content-length', 0))  # Total size in bytes

    if response.status_code == 200:
        # Show a progress bar while downloading
        with open(file_path, 'wb') as f, tqdm(
                desc=episode_title,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
            for chunk in response.iter_content(1024):
                if chunk:  # Filter out keep-alive new chunks
                    f.write(chunk)
                    bar.update(len(chunk))
        print(f"Podcast '{episode_title}' downloaded successfully.")

        # Mark the episode as downloaded in the database
        mark_episode_as_downloaded(db_cursor, db_conn, episode_title, episode_url, episode_published)
    else:
        print(f"Failed to download the episode: {response.status_code}")

# Download the 5 most recent episodes for a podcast
def download_podcast(podcast_url, db_conn, db_cursor, download_dir="podcasts", num_episodes=5):
    # Parse the RSS feed
    feed = feedparser.parse(podcast_url)
    
    # Check if the feed is valid
    if not feed.entries:
        print(f"Failed to retrieve podcast feed. Check the URL: {podcast_url}")
        return

    # Get the most recent `num_episodes` episodes
    recent_episodes = feed.entries[:num_episodes]

    # Download each episode
    for episode in recent_episodes:
        episode_title = episode.title
        episode_url = episode.enclosures[0]['url']
        episode_published = episode.published if 'published' in episode else 'Unknown'

        # Convert the published date to a formatted string if available
        try:
            episode_published = datetime(*episode.published_parsed[:6]).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print(f"Error parsing the date for episode '{episode_title}': {e}")

        # Download each episode if not already downloaded
        download_episode(episode_title, episode_url, download_dir, db_conn, db_cursor, episode_published)

# Read podcast feed URLs from config file
def get_podcast_feed_urls(config_file="config.ini"):
    config = configparser.ConfigParser()
    config.read(config_file)

    try:
        # Read and split the URLs into a list
        feed_urls = config['Podcasts']['feed_urls'].split(',')
        return [url.strip() for url in feed_urls]
    except KeyError:
        print("Failed to read the podcast feed URLs from the config file.")
        return []

if __name__ == "__main__":
    # Read the podcast feed URLs from config.ini
    podcast_urls = get_podcast_feed_urls()

    if podcast_urls:
        # Setup database connection
        db_conn, db_cursor = setup_db()
    
        # Download the 5 most recent episodes for each podcast
        for podcast_url in podcast_urls:
            print(f"Checking for new episodes from: {podcast_url}")
            download_podcast(podcast_url, db_conn, db_cursor, num_episodes=5)

        # Close the database connection
        db_conn.close()
    else:
        print("No valid podcast URLs found in the configuration.")
