from moviepy.editor import *
from moviepy.video.tools.segmenting import findObjects
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import tempfile
from elevenlabs import generate, save, set_api_key
from pydub import AudioSegment
import time

def create_text_image(text, size=(1080, 1920), fontsize=150, color='white'):
    """Create a text image using PIL instead of ImageMagick"""
    # Create a new image with a transparent background
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", fontsize)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
        fontsize = int(fontsize * 0.5)  # Scale down size for default font
    
    # Handle multiline text
    lines = text.split('\n')
    total_height = 0
    line_heights = []
    max_width = 0
    
    # Calculate total height and individual line heights
    for line in lines:
        # Get the bounding box for each line
        left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
        text_width = right - left
        text_height = bottom - top
        line_heights.append((text_width, text_height))
        total_height += text_height
        max_width = max(max_width, text_width)
    
    # If text is too wide, scale down the font size
    if max_width > size[0] * 0.9:  # Leave 10% margin
        scale_factor = (size[0] * 0.9) / max_width
        fontsize = int(fontsize * scale_factor)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", fontsize)
        except:
            font = ImageFont.load_default()
            fontsize = int(fontsize * 0.5)
        
        # Recalculate with new font size
        line_heights = []
        total_height = 0
        for line in lines:
            left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
            text_width = right - left
            text_height = bottom - top
            line_heights.append((text_width, text_height))
            total_height += text_height
    
    # Draw each line centered
    current_y = (size[1] - total_height) // 2
    for i, line in enumerate(lines):
        text_width, text_height = line_heights[i]
        x = (size[0] - text_width) // 2
        draw.text((x, current_y), line, font=font, fill=color)
        current_y += text_height
    
    return np.array(img)

def create_text_clip_with_effects(text, duration, fontsize=150, color='white'):
    """Create a text clip with snappy word-by-word animation"""
    words = text.split()
    word_clips = []
    
    # Much faster animations
    word_duration = 0.3  # How long each word stays
    word_delay = 0.25   # Delay before next word
    fade_duration = 0.1 # Quick fade in/out
    
    for i, word in enumerate(words):
        img = create_text_image(word, fontsize=fontsize, color=color)
        start_time = i * word_delay
        word_clip = ImageClip(img).set_duration(word_duration)
        
        # Faster bounce effect
        def make_bounce(t, initial_scale=0.5):
            if t < fade_duration:
                scale = 1 + (initial_scale - 1) * np.exp(-20*t) * np.cos(2*np.pi*6*t)
                return scale
            return 1
        
        word_clip = (word_clip
            .set_position(('center', 'center'))
            .set_start(start_time)
            .resize(lambda t: make_bounce(t))
            .fadein(fade_duration)
            .fadeout(fade_duration))
        
        word_clips.append(word_clip)
    
    total_duration = len(words) * word_delay + word_duration
    return CompositeVideoClip(word_clips, size=(1080, 1920)).set_duration(min(duration, total_duration))

def create_animated_text(text, duration, fontsize=150, color='white', bg_zoom=1.05):
    """Create an animated text clip with snappy line-by-line animation"""
    try:
        lines = text.split('\n')
        line_clips = []
        
        # Faster line transitions
        line_duration = 1.2  # Shorter duration for each line sequence
        line_delay = 1.3    # Quick transition to next line
        
        for i, line in enumerate(lines):
            start_time = i * line_delay
            line_clip = create_text_clip_with_effects(line, line_duration, fontsize, color)
            
            line_clip = (line_clip
                .set_position(('center', 'center'))
                .set_start(start_time))
            
            line_clips.append(line_clip)
        
        total_duration = len(lines) * line_delay
        return CompositeVideoClip(line_clips, size=(1080, 1920)).set_duration(min(duration, total_duration))
    
    except Exception as e:
        print(f"Error creating animated text: {str(e)}")
        return ColorClip(size=(1080, 1920), color=(0,0,0,0)).set_duration(duration)

def create_emoji_animation(emojis, duration):
    """Create bouncing emoji animation"""
    try:
        clips = []
        for i, emoji in enumerate(emojis):
            # Replace emojis with simple text alternatives
            emoji_text = {
                '😊': ':)',
                '🤖': '[BOT]',
                '💻': '[PC]',
                '🎭': '[MASK]',
                '🎪': '[SHOW]'
            }.get(emoji, '?')
            
            img = create_text_image(emoji_text, fontsize=200, color='white')
            txt = ImageClip(img).set_duration(duration/len(emojis))
            
            # Add bounce effect
            def bounce(t):
                return ('center', 200 + np.sin(8*t)*50)
            
            txt = txt.set_position(bounce)
            txt = txt.crossfadein(0.2).crossfadeout(0.2)
            clips.append(txt)
        
        return concatenate_videoclips(clips)
    except Exception as e:
        print(f"Error creating emoji animation: {str(e)}")
        return ColorClip(size=(1080, 1920), color=(0,0,0)).set_duration(duration)

def resize_video_portrait(clip, target_height=1920):
    """Resize and crop video to portrait mode (9:16 aspect ratio)"""
    # Calculate new width to maintain aspect ratio
    aspect_ratio = 9/16  # Portrait mode aspect ratio
    target_width = int(target_height * aspect_ratio)  # Should be 1080 for 1920 height
    
    # Resize video to be tall enough
    h = clip.h
    w = clip.w
    
    # First, resize to match target height
    scale = target_height / h
    resized_clip = clip.resize(height=target_height)
    
    # If the width is too narrow, resize based on width instead
    if resized_clip.w < target_width:
        scale = target_width / w
        resized_clip = clip.resize(width=target_width)
    
    # Crop to center
    x_center = resized_clip.w/2
    cropped_clip = resized_clip.crop(
        x_center=x_center,
        y_center=resized_clip.h/2,
        width=target_width,
        height=target_height
    )
    
    return cropped_clip

def create_narration(text, filename, voice="Adam", max_retries=3, retry_delay=3600):
    """Create narration using ElevenLabs API with retry mechanism"""
    try:
        # If file already exists, skip generation
        if os.path.exists(filename):
            print(f"Using existing audio file: {filename}")
            return True
            
        # Get API key from environment variable
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key:
            raise ValueError("Please set ELEVENLABS_API_KEY environment variable")
        
        set_api_key(api_key)
        
        for attempt in range(max_retries):
            try:
                # Generate audio
                audio = generate(
                    text=text,
                    voice=voice,
                    model="eleven_monolingual_v1"
                )
                
                # Save the audio file
                save(audio, filename)
                print(f"Successfully created narration: {filename}")
                return True
                
            except Exception as e:
                if "rate limit exceeded" in str(e).lower():
                    remaining_attempts = max_retries - attempt - 1
                    if remaining_attempts > 0:
                        print(f"Rate limit hit. Waiting {retry_delay} seconds before retry. {remaining_attempts} attempts remaining.")
                        time.sleep(retry_delay)
                        continue
                raise e
                
    except Exception as e:
        print(f"Error creating narration: {str(e)}")
        return False

def create_video():
    try:
        # Create narrations first to get timing
        os.makedirs("assets/audio", exist_ok=True)
        
        narrations = {
            "scene1": {
                "text": "Can robots really feel the ouch?",
                "file": "assets/audio/scene1.mp3"
            },
            "scene2a": {
                "text": "AI doesn't feel. It's just a really good actor.",
                "file": "assets/audio/scene2a.mp3"
            },
            "scene2b": {
                "text": "Think of it as the ultimate poker face.",
                "file": "assets/audio/scene2b.mp3"
            },
            "scene3": {
                "text": "Sometimes all we need is a kind word.",
                "file": "assets/audio/scene3.mp3"
            }
        }
        
        # Generate all narrations with progress tracking
        print("\nGenerating narrations...")
        for i, (name, scene) in enumerate(narrations.items(), 1):
            print(f"\nProcessing narration {i}/{len(narrations)}: {name}")
            if not os.path.exists(scene["file"]):
                success = create_narration(scene["text"], scene["file"])
                if not success:
                    print(f"Failed to create narration for {name}. You can:")
                    print("1. Wait an hour and try again")
                    print("2. Use existing audio files if available")
                    print("3. Continue without audio (video only)")
                    choice = input("Enter your choice (1/2/3): ")
                    
                    if choice == "1":
                        print("Please run the script again after an hour.")
                        return
                    elif choice == "2":
                        if not os.path.exists(scene["file"]):
                            print(f"No existing audio file found for {name}")
                            return
                        print(f"Using existing audio file for {name}")
                    else:
                        print("Continuing without audio...")
                        scene["duration"] = 4.0  # Default duration
                        continue
            else:
                print(f"Using existing audio file: {scene['file']}")
        
        # Get audio durations
        print("\nCalculating audio durations...")
        for scene in narrations.values():
            if os.path.exists(scene["file"]):
                audio = AudioSegment.from_mp3(scene["file"])
                scene["duration"] = len(audio) / 1000.0  # Convert to seconds
                print(f"Duration: {scene['duration']:.2f}s")
            else:
                scene["duration"] = 4.0  # Default duration if no audio
                print("Using default duration: 4.0s")
        
        # Scene 1: Frustrated person
        scene1 = VideoFileClip("assets/videos/frustrated_person.mp4").subclip(0, max(4, narrations["scene1"]["duration"]))
        scene1 = resize_video_portrait(scene1)
        text1 = create_animated_text(
            "Can robots\nreally feel\nthe ouch?", 
            narrations["scene1"]["duration"])
        audio1 = AudioFileClip(narrations["scene1"]["file"])
        
        # Scene 2: Robot processing
        scene2_duration = narrations["scene2a"]["duration"] + narrations["scene2b"]["duration"]
        scene2 = VideoFileClip("assets/videos/robot_processing.mp4").subclip(0, max(8, scene2_duration))
        scene2 = resize_video_portrait(scene2)
        text2 = create_animated_text(
            "AI doesn't feel\nIt's just a really\ngood actor",
            narrations["scene2a"]["duration"])
        text2b = create_animated_text(
            "Think of it as\nthe ultimate\npoker face",
            narrations["scene2b"]["duration"]).set_start(narrations["scene2a"]["duration"])
        audio2a = AudioFileClip(narrations["scene2a"]["file"])
        audio2b = AudioFileClip(narrations["scene2b"]["file"]).set_start(narrations["scene2a"]["duration"])
        
        # Scene 3: Chatbot interaction
        scene3 = VideoFileClip("assets/videos/chatbot_interaction.mp4").subclip(0, max(4, narrations["scene3"]["duration"]))
        scene3 = resize_video_portrait(scene3)
        text3 = create_animated_text(
            "Sometimes\nall we need is\na kind word",
            narrations["scene3"]["duration"])
        audio3 = AudioFileClip(narrations["scene3"]["file"])
        
        # Composite scenes with audio
        comp1 = CompositeVideoClip([scene1, text1]).set_audio(audio1)
        comp2 = CompositeVideoClip(
            [scene2, text2, text2b],
            size=(1080, 1920)
        ).set_audio(CompositeAudioClip([audio2a, audio2b]))
        comp3 = CompositeVideoClip([scene3, text3]).set_audio(audio3)
        
        # Create final video
        final = concatenate_videoclips([comp1, comp2, comp3], method="compose")
        
        final.write_videofile(
            "robot_emotions.mp4",
            fps=30,
            codec='libx264',
            audio_codec='aac',
            preset='medium'
        )
        
    except Exception as e:
        print(f"Error creating video: {str(e)}")

if __name__ == "__main__":
    create_video()
