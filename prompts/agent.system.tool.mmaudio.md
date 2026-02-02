### mmaudio:
**VIDEO TO AUDIO** - Generate audio/sound effects from video content.
Uses MMAudio model to create matching audio for silent videos.

**Parameters:**
- video: (required) URL to the video file
- prompt: (required) Description of the audio to generate
- negative_prompt: (optional) What to avoid in the audio
- seed: (optional) Random seed, -1 for random
- duration: (optional) Audio duration in seconds, 0 = auto from video

**Use cases:**
- Add sound effects to silent videos
- Generate ambient audio for footage
- Create background music for content
- Add realistic sounds to AI-generated videos

### Generate audio for a video:
~~~json
{
    "thoughts": [
        "User has a video that needs audio",
        "I'll use MMAudio to generate matching sound"
    ],
    "headline": "Generating audio for video",
    "tool_name": "mmaudio",
    "tool_args": {
        "video": "https://example.com/video.mp4",
        "prompt": "horse galloping on grass, hoofbeats, outdoor ambience"
    }
}
~~~

### Generate with specific style:
~~~json
{
    "thoughts": ["Creating cinematic audio for this footage"],
    "headline": "Generating cinematic audio",
    "tool_name": "mmaudio",
    "tool_args": {
        "video": "https://example.com/city-timelapse.mp4",
        "prompt": "busy city ambience, traffic sounds, urban atmosphere, cinematic",
        "negative_prompt": "music, voice, speech"
    }
}
~~~

### Example prompts:
- "ocean waves crashing, seagulls, beach ambience"
- "forest sounds, birds chirping, wind through trees"
- "coffee shop ambience, gentle chatter, espresso machine"
- "thunderstorm, heavy rain, distant thunder"
- "footsteps on gravel, outdoor walking"
