### elevenlabs_tts:
**HIGH-QUALITY VOICE OVERS** - Generate professional voice overs using ElevenLabs.
Use when user needs audio narration, voice overs, or text-to-speech.

**Actions:**
- `speak` - Convert text to speech (default)
- `voices` - List available voices

**Parameters for speak:**
- text: (required) The text to convert to speech
- voice: (optional) Voice name or ID, default: "madam_lyn"
- model: (optional) "eleven_multilingual_v2" (best) or "eleven_turbo_v2_5" (fast)
- output: (optional) Output file path, default: auto-generated
- stability: (optional) 0.0-1.0, default: 0.5
- similarity: (optional) 0.0-1.0, default: 0.75

**Available Voices:**
- `madam_lyn` - Filipino female voice (default)
- `rachel` - American female
- `drew` - American male
- `sarah` - British female
- `charlie` - Australian male
- `emily` - American female (young)

### Generate voice over:
~~~json
{
    "thoughts": ["User needs a voice over for their content"],
    "headline": "Generating voice over with ElevenLabs",
    "tool_name": "elevenlabs_tts",
    "tool_args": {
        "action": "speak",
        "text": "Welcome to InnovateHub, your partner in digital transformation.",
        "voice": "madam_lyn"
    }
}
~~~

### Generate with custom output:
~~~json
{
    "thoughts": ["Creating audio file with specific name"],
    "headline": "Creating voice over",
    "tool_name": "elevenlabs_tts",
    "tool_args": {
        "action": "speak",
        "text": "This is a test of the voice synthesis system.",
        "voice": "sarah",
        "output": "tmp/my_voiceover.mp3",
        "model": "eleven_turbo_v2_5"
    }
}
~~~

### List available voices:
~~~json
{
    "thoughts": ["Let me check what voices are available"],
    "headline": "Listing ElevenLabs voices",
    "tool_name": "elevenlabs_tts",
    "tool_args": {
        "action": "voices"
    }
}
~~~
