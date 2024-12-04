from moviepy.editor import *
from moviepy.video.tools.segmenting import findObjects
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

def create_text_image(text, size=(1080, 1920), fontsize=70, color='white'):
    """Create a text image using PIL instead of ImageMagick"""
    # Create a new image with a black background
    img = Image.new('RGB', size, (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Replace problematic characters with simpler alternatives
    text = text.replace('—', '-')  # Replace em dash with regular dash
    text = ''.join(char if ord(char) < 128 else '?' for char in text)  # Replace non-ASCII with ?
    
    # Use default font
    font = ImageFont.load_default()
    
    # Handle multiline text
    lines = text.split('\n')
    total_height = 0
    line_heights = []
    
    # Calculate total height and individual line heights
    for line in lines:
        # Get the bounding box for each line
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

def create_animated_text(text, duration, fontsize=70, color='white', bg_zoom=1.05):
    """Create an animated text clip with zoom effect and moving background"""
    try:
        # Create text image using PIL
        img = create_text_image(text, fontsize=fontsize, color=color)
        txt_clip = ImageClip(img).set_duration(duration)
        
        # Add fade and zoom animation
        txt_clip = txt_clip.crossfadein(0.5).crossfadeout(0.5)
        
        # Create moving background effect
        def move_text(t):
            return ('center', 480 + np.sin(3*t)*30)
        
        txt_clip = txt_clip.set_position(move_text)
        return txt_clip
    except Exception as e:
        print(f"Error creating animated text: {str(e)}")
        # Return a black clip as fallback
        return ColorClip(size=(1080, 1920), color=(0,0,0)).set_duration(duration)

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
            
            img = create_text_image(emoji_text, fontsize=100, color='white')
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

def create_video():
    try:
        # Scene 1: Frustrated person with animated text
        scene1 = VideoFileClip("assets/videos/frustrated_person.mp4").subclip(0, 7)
        scene1 = scene1.resize(height=1080)
        text1 = create_animated_text(
            "Can robots really feel the ouch?\nSpoiler: No way.", 7)
        
        # Composite scene 1
        comp1 = CompositeVideoClip([scene1, text1.set_position(('center', 'bottom'))])
        
        # Scene 2: Robot processing with emojis
        scene2 = VideoFileClip("assets/videos/robot_processing.mp4").subclip(0, 15)
        scene2 = scene2.resize(height=1080)
        text2 = create_animated_text(
            "AI doesn't feel.\nIt's just a really good actor,\nusing data to mimic emotions like a pro.", 7)
        text2b = create_animated_text(
            "Think of it as the ultimate poker face\n- no tears, just clever programming.", 8)
        emojis = create_emoji_animation(['😊', '🤖', '💻', '🎭', '🎪'], 15)
        
        # Composite scene 2
        comp2 = CompositeVideoClip([
            scene2,
            text2.set_position(('center', 'bottom')),
            text2b.set_start(7).set_position(('center', 'bottom')),
            emojis.set_position(('center', 0.2))
        ])
        
        # Scene 3: Chatbot interaction
        scene3 = VideoFileClip("assets/videos/chatbot_interaction.mp4").subclip(0, 8)
        scene3 = scene3.resize(height=1080)
        text3 = create_animated_text(
            "Does it work? Sure!\nSometimes, all we need is a kind word\n-even if it's fake.", 8)
        
        # Composite scene 3
        comp3 = CompositeVideoClip([scene3, text3.set_position(('center', 'bottom'))])
        
        # Final CTA with special animation
        cta = create_animated_text("Curious?\nDive into our blog.\nLink in bio", 5)
        
        # Final video
        final = concatenate_videoclips([comp1, comp2, comp3], method="compose")
        final = CompositeVideoClip([final, cta.set_start(final.duration-5).set_position(('center', 'bottom'))])
        
        # Add background music (optional)
        # audio = AudioFileClip("assets/audio/background_music.mp3")
        # final = final.set_audio(audio)
        
        # Write final video with high quality
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
