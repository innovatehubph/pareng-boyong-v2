# Empire Marketing Guide - PlataPay Agent Recruitment

## What is Empire?

**Empire** is PlataPay's marketing arm responsible for:
- Creating promotional content for agent/franchisee recruitment
- Managing social media marketing campaigns
- Generating ads for Facebook, Instagram, TikTok
- Tracking marketing performance

## PlataPay Agent Program

**PlataPay Agents** are:
- Outlet owners / Franchisees
- Sari-sari store owners who offer digital payment services
- Entrepreneurs who earn commission from transactions

**Services they offer:**
- Bills Payment (electricity, water, internet, etc.)
- E-Load (all networks)
- Remittance
- Bank Transfer
- QR Payments

## Using the Empire Ad Generator

When a user asks for PlataPay marketing content, use the `empire_ad_generator` tool.

### Example User Requests → Tool Action

| User Says | Tool Action |
|-----------|-------------|
| "Create a PlataPay ad" | `action="generate_full"` |
| "Generate marketing for Empire" | `action="generate_full"` |
| "Make a Facebook ad for PlataPay agents" | `action="generate_full", ad_type="facebook"` |
| "PlataPay Instagram post" | `action="generate_full", ad_type="instagram"` |
| "TikTok script for agent recruitment" | `action="generate_full", ad_type="tiktok"` |
| "Just the ad copy, no image" | `action="generate_copy"` |
| "Show me recent ads" | `action="list_ads"` |

### Common Themes for PlataPay Ads

1. **Extra Income** - "Dagdag kita" messaging
2. **Be Your Own Boss** - Entrepreneurship angle
3. **Low Capital** - Affordable franchise opportunity
4. **Financial Freedom** - Long-term financial goals
5. **Community Service** - Help your neighbors pay bills

### Target Audiences

- **Sari-sari store owners** - Already have customer traffic
- **OFW families** - Looking for passive income
- **Aspiring entrepreneurs** - Want to start a business
- **Stay-at-home parents** - Need flexible income
- **Students** - Part-time business opportunity

## Output Storage

All generated ads are saved to Google Sheets:
- **Spreadsheet:** PlataPay Agent Tracking
- **Sheet:** Ads
- **Columns:** Ad ID, Type, Theme, Target, Content, Promo, Status, Date, Image URL, Video URL

## Brand Guidelines

- **Name:** PlataPay
- **Tagline:** INNOVATING PAYMENTS
- **Tone:** Friendly, aspirational, Taglish (Filipino-English mix)
- **Colors:** Silver metallic, professional blue
- **Style:** Modern, trustworthy, approachable
