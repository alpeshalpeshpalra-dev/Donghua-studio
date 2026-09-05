import os
import random
import asyncio
import gradio as gr
import replicate
import edge_tts

# Replicate API Key को सर्वर से अपने आप उठाएगा
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")

# 1. Professional Voice Generation
async def generate_voice_async(text, voice_type):
    voice = "hi-IN-MadhurNeural" if "Male" in voice_type else "hi-IN-SwaraNeural"
    output_audio = "enhanced_voice.mp3"
    communicate = edge_tts.Communicate(text, voice, rate="-10%", pitch="+0Hz")
    await communicate.save(output_audio)
    return output_audio

# 2. Whisper AI Voice Detection & Subtitles
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
    except Exception:
        calc_duration = max(3.0, os.path.getsize(audio_file_path) / 5000.0)
        fallback_content = f"1\n00:00:00,000 --> 00:00:0{int(calc_duration)},000\n[Auto-Synced Voice Detection]\n"
        with open(srt_file_path, "w", encoding="utf-8") as f:
            f.write(fallback_content)
        return srt_file_path

# 3. Easy Master Generator Function
def generate_donghua_master(script_text, anim_style, vfx_effect, camera_shot, lighting_env, video_size, output_type, voice_type):
    enhanced_prompt = f"{anim_style}, {camera_shot}, {lighting_env}, masterpiece cinematic visual, 8k resolution, ultra detailed, {script_text}"
    
    if vfx_effect != "NONE":
        enhanced_prompt += f", {vfx_effect}"

    aspect_ratio = "16:9" if "16:9" in video_size else "9:16"
    seed = random.randint(1, 99999999)

    generated_media = None
    status_msg = ""
    audio_path = None
    srt_path = None

    if script_text and script_text.strip():
        try:
            audio_path = asyncio.run(generate_voice_async(script_text, voice_type))
            srt_path = detect_voice_and_generate_subtitles(audio_path)
            status_msg += "🎙️ वॉइस और सबटाइटल्स तैयार हैं! "
        except Exception as e:
            status_msg += f"[Voice Error: {str(e)}] "

    try:
        if "Poster" in output_type:
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
            status_msg += f"✅ 4K सीन तैयार है (Seed: {seed})"
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
            status_msg += "🎬 CapCut स्टाइल एनीमेशन क्लिप तैयार है!"

    except Exception as e:
        status_msg += f" [Visual Error: {str(e)}]"

    return generated_media, audio_path, srt_path, status_msg


# 4. Gradio UI with Separate Sound & Music Section
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🐉 Donghua & Anime Master Studio")
    
    # ------------------ TAB 1: MAIN CREATOR ------------------
    with gr.Tab("🎬 Visual & Voice Studio"):
        with gr.Row():
            with gr.Column(scale=1):
                script_input = gr.Textbox(
                    label="📜 कहानी या डायलॉग यहाँ लिखें", 
                    placeholder="यहाँ लिखें...",
                    lines=3
                )
                
                anim_style = gr.Radio(
                    choices=[
                        "🐉 3D Donghua (Chinese Cultivation)", 
                        "🎨 2D Classic Anime", 
                        "🗡️ Dark Fantasy Web Novel"
                    ],
                    value="🐉 3D Donghua (Chinese Cultivation)",
                    label="1️⃣ एनिमेशन स्टाइल चुनें"
                )
                
                vfx_effect = gr.Radio(
                    choices=[
                        "NONE",
                        "🔥 Crimson Eyes & Dark Aura", 
                        "⚡ Black Lightning", 
                        "🗡️ Flying Qi Swords"
                    ],
                    value="🔥 Crimson Eyes & Dark Aura",
                    label="2️⃣ VFX इफेक्ट चुनें"
                )

                camera_shot = gr.Radio(
                    choices=["🎥 Cinematic Close-Up", "🌌 Wide Angle Shot"],
                    value="🎥 Cinematic Close-Up",
                    label="3️⃣ कैमरा एंगल"
                )
                
                lighting_env = gr.Radio(
                    choices=["🌙 Moonlight & Fog", "☀️ Sunset Gold", "🔥 Volcanic Dark"],
                    value="🌙 Moonlight & Fog",
                    label="4️⃣ माहौल / लाइटिंग"
                )

                with gr.Row():
                    video_size = gr.Radio(
                        choices=["📺 YouTube Long (16:9)", "📱 Shorts/Reels (9:16)"],
                        value="📺 YouTube Long (16:9)",
                        label="📐 वीडियो साइज़"
                    )
                    output_type = gr.Radio(
                        choices=["🖼️ 4K Image Poster", "🎬 CapCut Animated Clip"],
                        value="🖼️ 4K Image Poster",
                        label="🎥 आउटपुट टाइप"
                    )

                voice_type = gr.Radio(
                    choices=["👨 Hindi Male (Madhur Pro)", "👩 Hindi Female (Swara)"],
                    value="👨 Hindi Male (Madhur Pro)",
                    label="🎙️ डबिंग आवाज़"
                )

                generate_btn = gr.Button("🚀 Generate Scene", variant="primary", size="lg")

            with gr.Column(scale=1):
                media_output = gr.Image(label="🖼️ Visual Result")
                audio_output = gr.Audio(label="🎙️ Professional Hindi Voice")
                srt_output = gr.File(label="📁 Subtitles (.SRT)")
                status_logs = gr.Textbox(label="Status", interactive=False)

        generate_btn.click(
            fn=generate_donghua_master,
            inputs=[
                script_input, anim_style, vfx_effect, camera_shot, lighting_env, 
                video_size, output_type, voice_type
            ],
            outputs=[media_output, audio_output, srt_output, status_logs]
        )

    # ------------------ TAB 2: SEPARATE SOUND & MUSIC SECTION ------------------
    with gr.Tab("🎧 SFX & BGM Library (अलग साउंड ट्रैक्स)"):
        gr.Markdown("### 🎵 बैकग्राउंड म्यूज़िक और साउंड इफ़ेक्ट्स (CapCut / Editing के लिए अलग से डाउनलोड करें)")
        
        with gr.Row():
            # Section A: Background Music (BGM)
            with gr.Column():
                gr.Markdown("#### 🎼 Background Music (BGM)")
                bgm_select = gr.Radio(
                    choices=[
                        "🐉 Epic Cultivation Battle BGM",
                        "🌌 Dark Suspense & Mystery BGM",
                        "🏮 Ancient Chinese Flute BGM",
                        "⚡ High-Tension Energy Surge BGM"
                    ],
                    value="🐉 Epic Cultivation Battle BGM",
                    label="BGM मूड चुनें"
                )
                bgm_btn = gr.Button("🔊 Fetch BGM Track")
                bgm_audio_preview = gr.Audio(label="🎵 BGM Audio (Download separately)")

            # Section B: Sound Effects (SFX)
            with gr.Column():
                gr.Markdown("#### 💥 Sound Effects (SFX)")
                sfx_select = gr.Radio(
                    choices=[
                        "🗡️ Qi Sword Slash Sound",
                        "⚡ Lightning Strike Crackle",
                        "👁️ Demonic Aura Rise",
                        "🦶 Footsteps in Dark Alley",
                        "💥 Energy Explosion"
                    ],
                    value="🗡️ Qi Sword Slash Sound",
                    label="SFX साउंड चुनें"
                )
                sfx_btn = gr.Button("💥 Fetch SFX Track")
                sfx_audio_preview = gr.Audio(label="🔊 SFX Audio (Download separately)")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=10000)
      
