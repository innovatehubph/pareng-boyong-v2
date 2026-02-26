---
name: platapay-marketing
description: Generate PlataPay marketing content - social posts, ads, promotional materials with brand guidelines.
version: 1.0.0
author: InnovateHub
tags:
  - marketing
  - platapay
  - content
  - social-media
  - branding
triggers:
  - platapay content
  - platapay marketing
  - platapay ad
  - platapay post
allowed_tools:
  - code_execution_tool
  - multimodal_generator
---

# PlataPay Marketing

Generate on-brand marketing content for PlataPay.

## Brand Guidelines

- **Colors:** Silver/metallic gradient, professional fintech aesthetic
- **Tagline:** "INNOVATING PAYMENTS"
- **Logo:** `/a0/assets/logos/platapay-favicon.png`
- **Website:** https://platapay.ph

## Usage

### Generate Social Post
```python
response = platapay_marketing(
    action="social_post",
    platform="facebook",  # or twitter, instagram
    topic="new feature",
    tone="professional"
)
```

### Generate Ad Copy
```python
response = platapay_marketing(
    action="ad_copy",
    campaign="agent_recruitment",
    target_audience="business_owners"
)
```

### Generate Image Ad
```python
response = platapay_marketing(
    action="image_ad",
    headline="Become a PlataPay Agent",
    subtext="Earn while helping your community"
)
```
