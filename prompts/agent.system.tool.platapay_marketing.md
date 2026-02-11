### platapay_marketing:
**PLATAPAY MARKETING AUTOMATION** - Trigger marketing workflows for agent recruitment and engagement.
Use this tool to automate email sequences, process referrals, and post to social media.

**Actions:**
- `agent_welcome` - Trigger 6-email welcome sequence for new agents
- `referral` - Process agent referral and calculate rewards
- `social_post` - Post to social media (Facebook, Twitter, Instagram)
- `status` - Check recent campaign executions

---

### Send welcome emails to new agent:
~~~json
{
    "thoughts": ["New agent signed up, triggering welcome email sequence"],
    "headline": "Sending agent welcome emails",
    "tool_name": "platapay_marketing",
    "tool_args": {
        "action": "agent_welcome",
        "email": "newagent@example.com",
        "name": "Juan Dela Cruz",
        "phone": "09171234567",
        "city": "Manila",
        "referred_by": "AGT-001"
    }
}
~~~

### Process approved referral:
~~~json
{
    "thoughts": ["Agent referred someone who got approved, processing reward"],
    "headline": "Processing referral reward",
    "tool_name": "platapay_marketing",
    "tool_args": {
        "action": "referral",
        "referrer_id": "AGT-001",
        "referrer_email": "agent@example.com",
        "referrer_name": "Maria Santos",
        "new_agent_email": "newagent@example.com",
        "new_agent_name": "Pedro Cruz",
        "status": "approved"
    }
}
~~~

### Post to social media:
~~~json
{
    "thoughts": ["Time to post recruitment content on Facebook"],
    "headline": "Posting to Facebook",
    "tool_name": "platapay_marketing",
    "tool_args": {
        "action": "social_post",
        "platform": "facebook",
        "category": "recruitment"
    }
}
~~~

---

**Referral Reward Structure:**
| Status | Referrer Gets | New Agent Gets |
|--------|---------------|----------------|
| Approved | ₱500 | ₱200 |
| First Transaction | +₱100 | - |
| 5 Referrals | +₱1,000 milestone | - |
| 10 Referrals | +₱2,500 milestone | - |
| 25 Referrals | +₱7,500 milestone | - |
| 50 Referrals | +₱20,000 milestone | - |

**Social Content Categories:**
- `recruitment` - Agent recruitment posts
- `features` - Product feature highlights
- `tips` - Agent business tips
- `promos` - Promotions and offers
