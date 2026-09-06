
import os
import random
import asyncio
import gradio as gr
import replicate
import edge_tts

REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")

# Voiceover Generator
async def generate_voice_async(text, voice_type, pitch_val, speed_val):
    voice = "hi-IN-MadhurNeural" if "Male" in voice_type else "hi-IN-SwaraNeural"
    output_audio = "enhanced_voice.mp3"
    communicate = edge_tts.Communicate(text, voice, pitch=f"{pitch_val}Hz", rate=f"{speed_val}%")
    await communicate.save(output_audio)
    return output_audio

# NAYA FEATURE: Quick Voice Sample Preview Function
async def preview_voice_sample(voice_type):
    voice = "hi-IN-MadhurNeural" if "Male" in voice_type else "hi-IN-SwaraNeural"
    sample_text = "नमस्ते, यह इस आवाज़ का सैंपल है। आप इसे चेक कर सकते हैं।"
    sample_file = "voice_sample.mp3"
    communicate = edge_tts.Communicate(sample_text, voice)
    await communicate.save(sample_file)
    return sample_file

def play_voice_sample(voice_type):
    return asyncio.run(preview_voice_sample(voice_type))

# Subtitle Generator
def generate_subtitles(audio_file_path, text):
    srt_file_path = "voice_synced_subtitles.srt"
    calc_duration = max(3.0, len(text) * 0.15) if text else 3.0
    fallback_content = f"1\n00:00:00,000 --> 00:00:0{int(calc_duration)},000\n{text if text else '[Auto Subtitle]'}\n"
    with open(srt_file_path, "w", encoding="utf-8") as f:
        f.write(fallback_content)
    return srt_file_path

# Storyboard Writer
def generate_ai_script(concept):
    if not concept.strip():
        return "कृपया अपनी कहानी का एक छोटा आइडिया लिखें।"
    return f"🎬 **AI स्टोरीबोर्ड (3 सीन्स):**\n\n1️⃣ **सीन 1:** {concept} की शुरुआत (Cinematic Close-Up)\n   - *डायलॉग:* 'यह जंग अभी खत्म नहीं हुई है!'\n\n2️⃣ **सीन 2:** महायुद्ध या ऊर्जा का विस्फोट (Wide Angle 8K Shot)\n   - *डायलॉग:* 'मेरी शक्ति का सामना करो!'\n\n3️⃣ **सीन 3:** विजय या रहस्यमयी मोड़ (Volcanic Dark Glow)\n   - *डायलॉग:* 'भविष्य अब बदल चुका है...'"

# Master Generator
def generate_donghua_master(script_text, anim_style, quality_setting, char_seed, vfx_effect, camera_shot, lighting_env, video_size, output_type, voice_type, pitch_val, speed_val):
    enhanced_prompt = f"{anim_style}, {quality_setting}, {camera_shot}, {lighting_env}, masterpiece cinematic visual, ultra detailed"
    if script_text and script_text.strip():
        enhanced_prompt += f", {script_text.strip()}"
    if vfx_effect != "NONE":
        enhanced_prompt += f", {vfx_effect}"

    aspect_ratio = "16:9" if "16:9" in video_size else "9:16"
    seed = int(char_seed) if char_seed and str(char_seed).isdigit() else random.randint(1, 99999999)

    generated_media = None
    status_msg = ""
    audio_path = None
    srt_path = None

    if script_text and script_text.strip():
        try:
            audio_path = asyncio.run(generate_voice_async(script_text, voice_type, pitch_val, speed_val))
            srt_path = generate_subtitles(audio_path, script_text)
            status_msg += "🎙️ वॉइस और सबटाइटल्स तैयार हैं! "
        except Exception as e:
            status_msg += f"[Voice Error: {str(e)}] "

    try:
        if "Poster" in output_type:
            output = replicate.run(
                "black-forest-labs/flux-schnell",
                input={"prompt": enhanced_prompt, "aspect_ratio": aspect_ratio, "seed": seed}
            )
            generated_media = output[0] if isinstance(output, list) and len(output) > 0 else output
            status_msg += f"✅ {quality_setting} सीन तैयार है (Character Seed: {seed})"
        else:
            output = replicate.run(
                "lucataco/animatediff:be427321d5178094deebe12c244b7f43f0193188d3e264625ef3275727282b9a",
                input={"prompt": enhanced_prompt, "seed": seed, "num_frames": 16, "guidance_scale": 7.5}
            )
            generated_media = output
            status_msg += f"🎬 CapCut स्टाइल एनीमेशन क्लिप ({quality_setting}) तैयार है!"
    except Exception as e:
        status_msg += f" [Visual Error: {str(e)}]"

    return generated_media, audio_path, srt_path, status_msg

# Sound Libraries
BGM_LIBRARY = {
    "🐉 Epic Cultivation Battle BGM": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    "🌌 Dark Suspense & Mystery BGM": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
    "🏮 Ancient Chinese Flute BGM": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
    "⚡ High-Tension Energy Surge BGM": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3"
}

SFX_LIBRARY = {
    "🗡️ Qi Sword Slash Sound": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
    "⚡ Lightning Strike Crackle": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3",
    "👁️ Demonic Aura Rise": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3",
    "🦶 Footsteps in Dark Alley": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-11.mp3",
    "💥 Energy Explosion": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-12.mp3"
}

def fetch_bgm(selected_bgm): return BGM_LIBRARY.get(selected_bgm, None)
def fetch_sfx(selected_sfx): return SFX_LIBRARY.get(selected_sfx, None)

# UI
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🐉 Donghua & Anime Master Studio (Pro Ultimate)")
    
    with gr.Tab("🎬 Visual & Voice Studio"):
        with gr.Row():
            with gr.Column(scale=1):
                script_input = gr.Textbox(label="📜 कहानी या डायलॉग यहाँ लिखें", placeholder="यहाँ लिखें...", lines=3)
                
                anim_style = gr.Radio(
                    choices=["🐉 3D Donghua (Chinese Cultivation)", "🎨 2D Classic Anime", "🗡️ Dark Fantasy Web Novel"],
                    value="🐉 3D Donghua (Chinese Cultivation)", label="1️⃣ एनिमेशन स्टाइल"
                )

                quality_setting = gr.Dropdown(
                    choices=["📱 Standard HD (1080p, 60fps)", "🖼️ Ultra HD (2K Dynamic)", "🌟 Cinematic 4K Master", "🌌 Ultra High 8K HDR Masterpiece"],
                    value="🌟 Cinematic 4K Master", label="🎞️ CapCut स्टाइल एक्सपोर्ट क्वालिटी"
                )

                char_seed = gr.Number(label="🆔 Character Seed (सेम चेहरा रखने के लिए आईडी दर्ज करें)", precision=0)
                vfx_effect = gr.Radio(choices=["NONE", "🔥 Crimson Eyes & Dark Aura", "⚡ Black Lightning", "🗡️ Flying Qi Swords"], value="🔥 Crimson Eyes & Dark Aura", label="2️⃣ VFX इफेक्ट")
                camera_shot = gr.Radio(choices=["🎥 Cinematic Close-Up", "🌌 Wide Angle Shot"], value="🎥 Cinematic Close-Up", label="3️⃣ कैमरा एंगल")
                lighting_env = gr.Radio(choices=["🌙 Moonlight & Fog", "☀️ Sunset Gold", "🔥 Volcanic Dark"], value="🌙 Moonlight & Fog", label="4️⃣ माहौल / लाइटिंग")

                with gr.Row():
                    video_size = gr.Radio(choices=["📺 YouTube Long (16:9)", "📱 Shorts/Reels (9:16)"], value="📺 YouTube Long (16:9)", label="📐 वीडियो साइज़")
                    output_type = gr.Radio(choices=["🖼️ Poster", "🎬 CapCut Animated Clip"], value="🖼️ Poster", label="🎥 आउटपुट टाइप")

                voice_type = gr.Radio(choices=["👨 Hindi Male (Madhur Pro)", "👩 Hindi Female (Swara)"], value="👨 Hindi Male (Madhur Pro)", label="🎙️ डबिंग आवाज़")

                # VOICE SAMPLE TEST BUTTON & PLAYER
                sample_btn = gr.Button("🔊 Test Voice Sample (आवाज़ का सैंपल सुनें)", variant="secondary")
                sample_audio_player = gr.Audio(label="🎧 Voice Sample Preview", interactive=False)
                sample_btn.click(fn=play_voice_sample, inputs=[voice_type], outputs=[sample_audio_player])

                with gr.Accordion("🎚️ Advanced Voice Controls (Pitch & Speed)", open=False):
                    pitch_val = gr.Slider(-10, 10, value=0, step=1, label="Voice Pitch")
                    speed_val = gr.Slider(-30, 30, value=0, step=5, label="Voice Speed %")

                generate_btn = gr.Button("🚀 Generate Master Scene", variant="primary", size="lg")

            with gr.Column(scale=1):
                media_output = gr.Image(label="🖼️ Visual Result")
                audio_output = gr.Audio(label="🎙️ Professional Hindi Voice")
                srt_output = gr.File(label="📁 Subtitles (.SRT)")
                status_logs = gr.Textbox(label="Status", interactive=False)

        generate_btn.click(
            fn=generate_donghua_master,
            inputs=[script_input, anim_style, quality_setting, char_seed, vfx_effect, camera_shot, lighting_env, video_size, output_type, voice_type, pitch_val, speed_val],
            outputs=[media_output, audio_output, srt_output, status_logs]
        )

    with gr.Tab("📝 AI Storyboard Writer"):
        gr.Markdown("### 🤖 एक लाइन का आइडिया लिखें और पूरा 3-सीन का स्टोरीबोर्ड पाएँ")
        concept_input = gr.Textbox(label="कहानी का छोटा आइडिया लिखें", placeholder="उदा: दो ड्रैगन राइडर्स की रात में लड़ाई...")
        storyboard_btn = gr.Button("✨ Write Storyboard", variant="secondary")
        storyboard_output = gr.Markdown()
        storyboard_btn.click(fn=generate_ai_script, inputs=[concept_input], outputs=[storyboard_output])

    with gr.Tab("🎧 SFX & BGM Library"):
        gr.Markdown("### 🎵 बैकग्राउंड म्यूज़िक और साउंड इफ़ेक्ट्स (सुनें और डाउनलोड करें)")
        with gr.Row():
            with gr.Column():
                gr.Markdown("#### 🎼 Background Music (BGM)")
                bgm_select = gr.Radio(choices=list(BGM_LIBRARY.keys()), value="🐉 Epic Cultivation Battle BGM", label="BGM मूड")
                bgm_btn = gr.Button("🔊 Fetch BGM Track")
                bgm_audio_preview = gr.Audio(label="🎵 BGM Preview")
                bgm_btn.click(fn=fetch_bgm, inputs=[bgm_select], outputs=[bgm_audio_preview])

            with gr.Column():
                gr.Markdown("#### 💥 Sound Effects (SFX)")
                sfx_select = gr.Radio(choices=list(SFX_LIBRARY.keys()), value="🗡️ Qi Sword Slash Sound", label="SFX साउंड")
                sfx_btn = gr.Button("💥 Fetch SFX Track")
                sfx_audio_preview = gr.Audio(label="🔊 SFX Preview")
                sfx_btn.click(fn=fetch_sfx, inputs=[sfx_select], outputs=[sfx_audio_preview])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=10000)
          
