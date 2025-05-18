import os
import re
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from openai import OpenAI
from moviepy import ImageClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips, vfx
from PIL import Image

# --- CONFIGURATION ---
PDF_PATH        = "My Mama is My Hero.pdf" # Add your PDF file path here
OUTPUT_DIR      = "output_pages"
VIDEO_FILENAME  = "book_presentation.mp4"
PAGE_DURATION   = 4     # seconds per page (including narration)
TRANSITION_SEC  = 1     # fade-in/out seconds
VIDEO_WIDTH     = 1280  # output width (height auto-scaled)
OPENAI_TTS_MODEL = "gpt-4o-mini-tts"       # OpenAI TTS model (e.g., "tts-1", "tts-1-hd")
OPENAI_TTS_VOICE = "shimmer"       # OpenAI TTS voice (e.g., "alloy", "echo", "fable", "onyx", "nova", "shimmer")

# Initialize OpenAI client
# Make sure your OPENAI_API_KEY environment variable is set.
# client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
# If you have it in a .env file and loaded it, it should be picked up automatically.
# Or, you can explicitly pass it:
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("Warning: OPENAI_API_KEY environment variable not found. TTS generation will likely fail.")
    # You could raise an error here or provide a default behavior if preferred
    # For now, we'll let it proceed and potentially fail at the API call.
client = OpenAI()


# --- STEP 1: Convert PDF pages to images ---
# --- STEP 2: Extract text for narration ---
# --- STEP 3: Build per-page clips (image + optional TTS) ---
 # 3a) Generate narration audio
 # 3b) Create image clip
 # 3c) Attach audio
 # 3d) Apply fade transitions
# --- STEP 4: Concatenate and export ---

def process_pdf(pdf_path, output_dir):
    """Converts PDF to images and extracts text per page."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    images = convert_from_path(pdf_path)
    reader = PdfReader(pdf_path)
    page_data = []

    for i, page_image in enumerate(images):
        page_num = i + 1
        image_path = os.path.join(output_dir, f"page_{page_num}.png")
        page_image.save(image_path, "PNG")

        text = ""
        if i < len(reader.pages):
            page_text = reader.pages[i].extract_text()
            # User's existing print for debugging, you might want to move it after all processing
            # print(f"Original text for page {page_num}: {page_text}") 
            if page_text:
                # 1. Replace newlines with spaces
                processed_text = page_text.replace('\n', ' ')

                # 2. Iteratively remove single spaces between letters to fix "M y M am a" -> "MyMama"
                temp_text = processed_text
                while True:
                    # This regex finds a letter, a single space, and another letter, and replaces it with the two letters.
                    corrected_text = re.sub(r'([a-zA-Z])\s([a-zA-Z])', r'\1\2', temp_text)
                    if corrected_text == temp_text: # No more changes means we're done with this step
                        break
                    temp_text = corrected_text
                processed_text = temp_text

                # 3. Normalize multiple spaces (now between words) to single spaces and strip.
                processed_text = re.sub(r'\s+', ' ', processed_text).strip()
                
                # 4. Remove page number patterns from the end of the string.
                processed_text = re.sub(r'(?:Page|Pg\.?|P\.?)?\s*\d+\s*$', '', processed_text, flags=re.IGNORECASE).strip()
                
                text = processed_text
                # print(f"Cleaned text for page {page_num}: '{text}'") # Optional: for checking cleaned text
        
        page_data.append({"image_path": image_path, "text": text, "page_num": page_num})
        print(f"Processed page {page_num}: Image saved to {image_path}, Text extracted: '{text[:50]}...'" )

    return page_data

def create_page_clip(page_data, output_dir, page_duration, transition_sec, video_width):
    """Creates a video clip for a single page with image, optional narration, and transitions."""
    image_path = page_data["image_path"]
    text = page_data["text"]
    page_num = page_data["page_num"]

    # 3a) Generate narration audio
    audio_clip = None
    narration_original_duration = 0 # Use this for calculations
    if text:
        tts_path = os.path.join(output_dir, f"page_{page_num}_audio.mp3")
        try:
            response = client.audio.speech.create(
                model=OPENAI_TTS_MODEL,
                voice=OPENAI_TTS_VOICE,
                input=text,
                instructions="Speak in a dramatic and comical voice. Be very excited and happy to be reading this book.",
            )
            response.stream_to_file(tts_path)
            audio_clip = AudioFileClip(tts_path)
            narration_original_duration = audio_clip.duration
            print(f"Page {page_num}: OpenAI TTS audio created: {tts_path} (Duration: {narration_original_duration:.2f}s)")
        except Exception as e:
            print(f"Page {page_num}: Error generating OpenAI TTS audio: {e}. Skipping audio for this page.")
            audio_clip = None
            narration_original_duration = 0

    # 3b) Create image clip
    with Image.open(image_path) as img:
        img_width, img_height = img.size
    aspect_ratio = img_height / img_width
    video_height = int(video_width * aspect_ratio)
    if video_height % 2 != 0:
        video_height +=1

    # Determine the final target duration for this page's video segment
    # This accounts for narration, transitions, and the configured PAGE_DURATION.
    target_clip_duration = max(page_duration, narration_original_duration + (2 * transition_sec))

    # Create the image clip with the final target duration
    img_clip = ImageClip(image_path, duration=target_clip_duration)
    img_clip = img_clip.resized(width=video_width, height=video_height)
    print(f"Page {page_num}: Image clip created. Target duration: {target_clip_duration:.2f}s. Size: {video_width}x{video_height}")

    # 3c) Attach audio, ensuring it matches target_clip_duration with narration centered
    if audio_clip:
        if narration_original_duration < target_clip_duration:
            # Narration is shorter than the target video duration, so center it with silence.
            start_time = (target_clip_duration - narration_original_duration) / 2.0
            centered_narration_clip = audio_clip.with_start(start_time)
            # Create a composite audio clip that spans the full target_clip_duration
            final_audio_for_page = CompositeAudioClip([centered_narration_clip]).with_duration(target_clip_duration)
        elif narration_original_duration > target_clip_duration:
            # Narration is somehow longer; trim it (should ideally not happen with current target_clip_duration logic)
            final_audio_for_page = audio_clip.subclip(0, target_clip_duration)
        else:
            # Narration duration matches target_clip_duration exactly
            final_audio_for_page = audio_clip
        
        img_clip = img_clip.with_audio(final_audio_for_page)
        print(f"Page {page_num}: Audio attached to image clip. Audio duration set to: {final_audio_for_page.duration:.2f}s")

    # 3d) Apply fade transitions
    # Ensure the clip duration is long enough for the fade transitions
    if target_clip_duration > (2 * transition_sec):
        img_clip = img_clip.with_effects([vfx.FadeIn(transition_sec)])
        img_clip = img_clip.with_effects([vfx.FadeOut(transition_sec)])
        print(f"Page {page_num}: Fade transitions applied ({transition_sec}s each).")
    else:
        print(f"Page {page_num}: Clip duration ({target_clip_duration:.2f}s) too short for full fade transitions ({2 * transition_sec}s). Skipping fades.")
        # If too short for both, maybe apply a shorter fade or just one if possible
        if target_clip_duration > transition_sec:
            # Calculate a safe fade duration for shorter clips
            actual_fade_duration = min(transition_sec, target_clip_duration / 2.0)
            img_clip = img_clip.with_effects([vfx.FadeIn(actual_fade_duration)])
            img_clip = img_clip.with_effects([vfx.FadeOut(actual_fade_duration)])
            print(f"Page {page_num}: Applied shorter fade transitions ({actual_fade_duration:.2f}s each).")

    # Set the final duration of the clip, including transitions (safeguard)
    img_clip = img_clip.with_duration(target_clip_duration)
    print(f"Page {page_num}: Final clip duration: {img_clip.duration:.2f}s")

    return img_clip

if __name__ == "__main__":
    # Create output directory for images and audio
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    all_page_data = process_pdf(PDF_PATH, OUTPUT_DIR)
    print(f"\n--- PDF Processing Complete. {len(all_page_data)} pages processed. ---")

    # Further steps will go here
    for data in all_page_data:
        print(f"Page {data['page_num']}: {data['image_path']}, Text: '{data['text'][:30]}...'" )

    print("\n--- STEP 3: Building per-page clips ---")
    all_clips = []
    for data in all_page_data:
        print(f"\nProcessing Page {data['page_num']}...")
        clip = create_page_clip(data, OUTPUT_DIR, PAGE_DURATION, TRANSITION_SEC, VIDEO_WIDTH)
        if clip:
            all_clips.append(clip)
    
    if not all_clips:
        print("No clips were created. Exiting.")
        exit()

    print("\n--- STEP 4: Concatenating clips and exporting video ---")
    final_video = concatenate_videoclips(all_clips, method="compose")
    
    # Define the output video path
    output_video_path = os.path.join(OUTPUT_DIR, VIDEO_FILENAME)

    # Export the final video
    try:
        print(f"Exporting final video to {output_video_path}...")
        # Added fps=24, common for video, and codec for wider compatibility
        final_video.write_videofile(output_video_path, codec="libx264", audio_codec="aac", fps=24)
        print(f"\n--- Video Export Complete: {output_video_path} ---")
    except Exception as e:
        print(f"Error exporting video: {e}")
    finally:
        # Clean up temporary audio files if any were created directly by moviepy
        for clip in all_clips:
            if clip.audio is not None and hasattr(clip.audio, 'filename') and clip.audio.filename:
                if os.path.exists(clip.audio.filename) and "_TEMP_MPY" in clip.audio.filename: # moviepy temp audio
                    try:
                        os.remove(clip.audio.filename)
                        print(f"Cleaned up temporary audio: {clip.audio.filename}")
                    except Exception as e_clean:
                        print(f"Error cleaning up temp audio {clip.audio.filename}: {e_clean}")
            # Clean up TTS audio files we created
            page_num = getattr(clip, 'page_num', None) # Need to ensure page_num is accessible or passed differently
            # This part of cleanup might be tricky if page_num isn't directly on the clip
            # For now, we rely on the known naming convention if we want to be more specific
            # A better way would be to store tts_path in page_data and pass it along

        # Clean up our generated TTS files
        for data in all_page_data:
            page_num = data["page_num"]
            tts_path = os.path.join(OUTPUT_DIR, f"page_{page_num}_audio.mp3")
            if os.path.exists(tts_path):
                try:
                    os.remove(tts_path)
                    print(f"Cleaned up TTS audio: {tts_path}")
                except Exception as e_clean:
                    print(f"Error cleaning up TTS audio {tts_path}: {e_clean}")
        print("Cleanup of generated audio files attempted.") 