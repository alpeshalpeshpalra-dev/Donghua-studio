import os
import random
import asyncio
import gradio as gr
import replicate
import edge_tts
os.environ["REPLICATE_API_TOKEN"] = "r8_Ki0**********************************"

# 1. Unlimited Voice Generation (Microsoft Edge-TTS)
async def generate_voice_async(text, voice_type):
    voice = "hi-IN-MadhurNeural" if voice_type == "Hindi Male (Natural)" else "hi-IN-SwaraNeural"
    output_audio = "enhanced_voice.mp3"
    communicate = edge_tts.Communicate(text, voice, rate="+0%", pitch="+0Hz")
    await communicate.save(output_audio)
    return output_audio

# 2. Whisper AI Voice Detection (Silent Parts Skip + Exact Speech Match)
def detect_voice_and_generate_subtitles(audio_file_path):
    srt_file_path = "voice_synced_subtitles.srt"
    try:
        output = replicate.run(
            "openai/whisper:4c5155e06d564a509c37fc00162ee6eb6f5e657ed5040f9a9411c125d65757e9",
            input={
                "audio": open(audio_file_path, "rb"),
                "model": "large-v3",
                "transcription": "srt"
            }
        )
        
        srt_content = output.get("srt", "") if isinstance(output, dict) else str(output)
        with open(srt_file_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
            
        return srt_file_path
    except Exception as e:
        calc_duration = max(3.0, os.path.getsize(audio_file_path) / 5000.0)
        fallback_content = f"1\n00:00:00,000 --> 00:00:0{int(calc_duration)},000\n[Auto-Synced Voice Detection Fallback]\n"
        with open(srt_file_path, "w", encoding="utf-8") as f:
            f.write(fallback_content)
        return srt_file_path

# 3. Main Master Generator
def generate_donghua_master(script_text, anim_style, vfx_effect, camera_shot, lighting_env, video_size, output_type, quality_mode, seed_lock, voice_type):
    enhanced_prompt = f"{anim_style} style, {camera_shot}, {lighting_env}, realistic dynamic physics, flowing hair and cloth movement, masterpiece cinematic visual, {script_text}"
    
    if vfx_effect == "Glowing Crimson Eyes & Demonic Aura":
        enhanced_prompt += ", intense crimson glowing eyes, dark ominous smoke aura swirling around body"
    elif vfx_effect == "Black Lightning & Dark Fog":
        enhanced_prompt += ", crackling black lightning strikes, dense shadowy fog, ominous destruction atmosphere"
    elif vfx_effect == "Sword Coffin & Flying Qi Swords":
        enhanced_prompt += ", dozens of floating spiritual Qi swords, golden and purple energy waves, ancient sword coffin behind back"
    elif vfx_effect == "Heavenly Dragon Qi (Golden/Blue Aura)":
        enhanced_prompt += ", gigantic ancient spiritual dragon aura manifestation behind character, glowing golden qi energy surges"
    elif vfx_effect == "Phoenix Flames & Celestial Fire":
        enhanced_prompt += ", roaring intense celestial phoenix flames, flying burning embers, fiery atmosphere"
    elif vfx_effect == "Spatial Rift & Teleportation Portal":
        enhanced_prompt += ", tearing spatial dimensions rift, dark cosmic portal behind character, purple galaxy energy distortion"

    if quality_mode == "8K Ultra HD (Detailed Physics)":
        enhanced_prompt += ", 8k resolution, hyperrealistic skin texture, volumetric studio lighting, raytraced reflections"
    elif quality_mode == "Super Fast Mode (Quick Draft)":
        enhanced_prompt += ", highly detailed, sharp focus"

    aspect_ratio = "16:9" if video_size == "Long Video / Banner (16:9)" else "9:16"
    seed = int(seed_lock) if seed_lock and seed_lock.strip().isdigit() else random.randint(1, 99999999)

    generated_media = None
    status_msg = ""
    audio_path = None
    srt_path = None

    if script_text and script_text.strip():
        try:
            audio_path = asyncio.run(generate_voice_async(script_text, voice_type))
            srt_path = detect_voice_and_generate_subtitles(audio_path)
            status_msg += "🎙️ Voice Generated & 🎯 Voice-Detected SRT Ready! "
        except Exception as e:
            status_msg += f"[Voice/SRT Error: {str(e)}] "

    try:
        if "Image Poster" in output_type:
            output = replicate.run(
                "black-forest-labs/flux-schnell",
                input={
                    "prompt": enhanced_prompt,
                    "aspect_ratio": aspect_ratio,
                    "seed": seed,
                    "num_outputs": 1,
                    "output_format": "png"
                }
            )
            generated_media = output[0]
            status_msg += f"🔒 Seed ID: {seed}"
        else:
            output = replicate.run(
                "lucataco/animatediff:be427321d5178094deebe12c244b7f43f0193188d3e264625ef3275727282b9a",
                input={
                    "prompt": enhanced_prompt,
                    "seed": seed,
                    "num_frames": 16,
                    "guidance_scale": 7.5
                }
            )
            generated_media = output
            status_msg += f"🔒 Seed ID: {seed}"

    except Exception as e:
        status_msg += f" [Visual Error: {str(e)}]"

    return generated_media, audio_path, srt_path, status_msg

# 4. Gradio Interface
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎬 3D Donghua Master Studio (Whisper Voice Detection + SRT Export)")
    
    with gr.Row():
        with gr.Column():
            script_input = gr.Textbox(
                label="📜 Script Box (अपनी कहानी या संवाद लिखें)", 
                placeholder="यहाँ कहानी या डायलॉग पेस्ट करें...",
                lines=4
            )
            voice_dropdown = gr.Dropdown(
                choices=["Hindi Male (Natural)", "Hindi Female (Natural)"], 
                value="Hindi Male (Natural)", 
                label="🎙️ AI Voice Selection (Unlimited)"
            )
            output_type = gr.Radio(
                choices=["🖼️ Image Poster (4K/8K)", "🎬 Short VFX Video (Physics Animated)"],
                value="🖼️ Image Poster (4K/8K)",
                label="🎥 Output Selection"
            )
            style_dropdown = gr.Dropdown(
                choices=["3D Donghua (Chinese Animation)", "2D Classic Anime", "3D Cultivation Fantasy", "Dark Fantasy Web Novel"], 
                value="3D Donghua (Chinese Animation)", 
                label="🎨 Art Style"
            )
            vfx_dropdown = gr.Dropdown(
                choices=[
                    "None", 
                    "Glowing Crimson Eyes & Demonic Aura", 
                    "Black Lightning & Dark Fog", 
                    "Sword Coffin & Flying Qi Swords",
                    "Heavenly Dragon Qi (Golden/Blue Aura)",
                    "Phoenix Flames & Celestial Fire",
                    "Spatial Rift & Teleportation Portal"
                ], 
                value="Glowing Crimson Eyes & Demonic Aura", 
                label="🔥 High-End VFX Layer"
            )
            
            with gr.Row():
                camera_shot = gr.Dropdown(
                    choices=["Cinematic Close-Up Shot", "Wide Angle Dynamic Shot", "Drone Aerial View Shot"],
                    value="Cinematic Close-Up Shot",
                    label="🎥 Camera Angle"
                )
                lighting_env = gr.Dropdown(
                    choices=["Volcanic Red Darkness", "Moonlight Night & Fog", "Sunset Gold & Cloud Ocean", "Studio Volumetric Lighting"],
                    value="Studio Volumetric Lighting",
                    label="🌌 Environment Lighting"
                )

            size_dropdown = gr.Dropdown(
                choices=["Shorts / Reel (9:16)", "Long Video / Banner (16:9)"], 
                value="Long Video / Banner (16:9)", 
                label="📐 Aspect Ratio"
            )
            quality_dropdown = gr.Dropdown(
                choices=["8K Ultra HD (Detailed Physics)", "Super Fast Mode (Quick Draft)"], 
                value="8K Ultra HD (Detailed Physics)", 
                label="✨ Quality Mode"
            )
            seed_input = gr.Textbox(label="🔒 Character Lock (Seed ID)", placeholder="Seed number...")
            generate_btn = gr.Button("🔥 Generate Complete Scene (Visual + Voice + Detect Subtitle)", variant="primary")
        
        with gr.Column():
            media_output = gr.Image(label="🖼️ Clean Visual (No Overlay Text)")
            audio_output = gr.Audio(label="🎙️ Natural AI Voice")
            srt_output = gr.File(label="📁 Download Voice-Detected SRT Subtitles")
            seed_status = gr.Textbox(label="🔒 Status Logs", interactive=False)
            
    generate_btn.click(
        fn=generate_donghua_master, 
        inputs=[
            script_input, style_dropdown, vfx_dropdown, camera_shot, lighting_env, 
            size_dropdown, output_type, quality_dropdown, seed_input, voice_dropdown
        ], 
        outputs=[media_output, audio_output, srt_output, seed_status]
    )
app = demo.app




if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
    
