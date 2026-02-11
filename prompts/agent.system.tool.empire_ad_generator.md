# empire_ad_generator

## ⚠️ IMPORTANT: VIDEO VS IMAGE ROUTING

**If user asks for VIDEO content, use `platapay_video_ads` instead!**

| Request Type | Tool to Use |
|--------------|-------------|
| "video ad", "TikTok", "Reels", "animate" | → `platapay_video_ads` |
| "image ad", "poster", "banner", "copy only" | → `empire_ad_generator` ✓ |

## WHEN TO USE THIS TOOL

**Use this tool for STATIC/IMAGE content:**
- Facebook/Instagram **image** posts
- Marketing **banners** and **posters**
- Ad **copy** generation only
- Static social media graphics

**DO NOT use for:**
- Video ads → use `platapay_video_ads`
- TikTok/Reels → use `platapay_video_ads`
- Animated content → use `platapay_video_ads`

**Trigger phrases for THIS tool:**
- "Create a PlataPay **image** ad"
- "Generate **banner** for PlataPay"
- "PlataPay **poster**"
- "Write **ad copy** for PlataPay"
- "Marketing **graphic** for PlataPay"

## WHAT THIS TOOL DOES

Generates **static marketing content** for PlataPay:
1. **Ad Copy** - Taglish (Filipino-English) marketing text
2. **Marketing Image** - AI-generated promotional image (FLUX)
3. **Saves to Google Sheets** - All content tracked in spreadsheet

## QUICK USAGE

### Generate Image Ad (most common):
~~~json
{
    "thoughts": ["User wants a static IMAGE ad for PlataPay"],
    "headline": "Creating PlataPay image ad",
    "tool_name": "empire_ad_generator",
    "tool_args": {
        "action": "generate_full",
        "theme": "extra income",
        "target": "sari-sari store owners",
        "ad_type": "facebook",
        "generate_video": false
    }
}
~~~

### Generate Ad Copy Only:
~~~json
{
    "thoughts": ["User only needs the text/copy for the ad"],
    "headline": "Generating ad copy",
    "tool_name": "empire_ad_generator",
    "tool_args": {
        "action": "generate_copy",
        "theme": "be your own boss",
        "target": "entrepreneurs",
        "ad_type": "instagram"
    }
}
~~~

### Generate Image Only:
~~~json
{
    "thoughts": ["User wants just the marketing image"],
    "headline": "Generating marketing image",
    "tool_name": "empire_ad_generator",
    "tool_args": {
        "action": "generate_image",
        "theme": "financial freedom",
        "target": "OFW families"
    }
}
~~~

## PARAMETERS

| Parameter | Default | Options |
|-----------|---------|---------|
| `action` | generate_full | generate_full, generate_copy, generate_image, list_ads, help |
| `theme` | extra income | extra income, be your own boss, financial freedom, community service |
| `target` | sari-sari store owners | entrepreneurs, OFW families, small business owners |
| `ad_type` | facebook | facebook, instagram, tiktok, story |
| `generate_video` | false | Set to false for image-only |

## TARGET AUDIENCES

- Sari-sari store owners
- Aspiring entrepreneurs
- OFW families
- Small business owners
- Stay-at-home parents

## GOOGLE SHEET

All generated ads saved to:
- **Spreadsheet ID:** 11GhQfg1zTEs1CfNcyGkqq7dLfnacIBbKVWss-PSXzlg
- **Sheet:** Empire Ads
