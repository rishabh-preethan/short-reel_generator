import os
import requests
from dotenv import load_dotenv

def download_video(url, filename):
    """Download a video file"""
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return True
    return False

def search_and_download_videos(api_key):
    """Search for and download required videos"""
    headers = {'Authorization': api_key}
    
    # Create assets directory if it doesn't exist
    os.makedirs('assets/videos', exist_ok=True)
    
    # Search queries and target filenames
    searches = [
        ('frustrated person computer', 'frustrated_person.mp4'),
        ('robot artificial intelligence', 'robot_processing.mp4'),
        ('person chatting online happy', 'chatbot_interaction.mp4')
    ]
    
    for query, filename in searches:
        print(f"Searching for {query}...")
        # Search for videos
        response = requests.get(
            f'https://api.pexels.com/videos/search?query={query}&per_page=1',
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['videos']:
                video = data['videos'][0]
                # Get the HD video file or the highest quality available
                video_file = next(
                    (f for f in video['video_files'] if f['quality'] == 'hd'),
                    video['video_files'][0]
                )
                
                print(f"Downloading {filename}...")
                # Download the video
                filepath = os.path.join('assets/videos', filename)
                if download_video(video_file['link'], filepath):
                    print(f'Successfully downloaded {filename}')
                else:
                    print(f'Failed to download {filename}')
            else:
                print(f'No videos found for {query}')
        else:
            print(f'Failed to search for {query}. Status code: {response.status_code}')

if __name__ == '__main__':
    load_dotenv()
    # Read API key from .env file
    with open('.env', 'r') as f:
        api_key = f.readline().strip().split('=')[1]
    
    if not api_key:
        print("Please set PEXELS_API_KEY in your .env file")
    else:
        print("Starting video download...")
        search_and_download_videos(api_key)
