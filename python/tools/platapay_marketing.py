"""
PlataPay Marketing Automation Tool for Pareng Boyong
Triggers n8n marketing workflows for agent recruitment, referrals, and social media
"""

import os
import json
import requests
from datetime import datetime
from python.helpers.tool import Tool, Response


class PlatapayMarketing(Tool):
    """
    Marketing automation for PlataPay.
    Triggers n8n workflows for various marketing campaigns.
    
    Actions:
    - agent_welcome: Trigger welcome email sequence for new agent
    - referral: Process agent referral
    - social_post: Trigger social media post
    - campaign_status: Check campaign/workflow status
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.n8n_base_url = os.environ.get("N8N_BASE_URL", "http://localhost:5678")
        self.n8n_api_key = os.environ.get("N8N_API_KEY", "")
        
        # Webhook endpoints
        self.webhooks = {
            "agent_welcome": f"{self.n8n_base_url}/webhook/platapay/agent-signup",
            "referral": f"{self.n8n_base_url}/webhook/platapay/referral",
            "social_post": f"{self.n8n_base_url}/webhook/platapay/social-post"
        }

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "").lower()
        
        actions = {
            "agent_welcome": self._trigger_agent_welcome,
            "welcome": self._trigger_agent_welcome,  # Alias
            "referral": self._trigger_referral,
            "refer": self._trigger_referral,  # Alias
            "social_post": self._trigger_social_post,
            "social": self._trigger_social_post,  # Alias
            "post": self._trigger_social_post,  # Alias
            "status": self._check_status,
            "help": self._show_help
        }
        
        if action not in actions:
            return await self._show_help()
        
        try:
            return await actions[action]()
        except Exception as e:
            return Response(
                message=f"Marketing automation error: {str(e)}",
                break_loop=False
            )

    async def _trigger_agent_welcome(self) -> Response:
        """Trigger welcome email sequence for a new agent."""
        email = self.args.get("email", "")
        name = self.args.get("name", "")
        phone = self.args.get("phone", "")
        city = self.args.get("city", "")
        referred_by = self.args.get("referred_by", "")
        
        if not email:
            return Response(
                message="Error: 'email' is required for agent welcome sequence.\n\n"
                        "Example: platapay_marketing action=agent_welcome email=agent@example.com name=\"Juan Dela Cruz\" city=Manila",
                break_loop=False
            )
        
        payload = {
            "email": email,
            "name": name or email.split("@")[0],
            "phone": phone,
            "city": city or "Philippines",
            "referred_by": referred_by
        }
        
        try:
            response = requests.post(
                self.webhooks["agent_welcome"],
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return Response(
                    message=f"""✅ **Agent Welcome Sequence Triggered!**

**Agent Details:**
- Name: {payload['name']}
- Email: {payload['email']}
- City: {payload['city']}
- Agent ID: {result.get('agent', {}).get('id', 'Assigned')}

**Email Sequence:**
- ✉️ Welcome email: Sent immediately
- 📧 Day 1: Getting Started tips
- 📧 Day 3: Top Agent tips
- 📧 Day 5: Support check-in
- 📧 Day 7: First week review
- 📧 Day 14: Upsell opportunities

{result.get('message', '')}""",
                    break_loop=False
                )
            else:
                return Response(
                    message=f"⚠️ Workflow trigger returned status {response.status_code}: {response.text}",
                    break_loop=False
                )
                
        except requests.exceptions.RequestException as e:
            return Response(
                message=f"⚠️ Could not reach n8n workflow: {str(e)}\n\n"
                        f"Make sure the workflow is active at: {self.webhooks['agent_welcome']}",
                break_loop=False
            )

    async def _trigger_referral(self) -> Response:
        """Process an agent referral."""
        referrer_id = self.args.get("referrer_id", "")
        referrer_email = self.args.get("referrer_email", "")
        referrer_name = self.args.get("referrer_name", "")
        new_agent_email = self.args.get("new_agent_email", "")
        new_agent_name = self.args.get("new_agent_name", "")
        status = self.args.get("status", "pending")  # pending, approved, first_transaction
        
        if not referrer_id or not new_agent_email:
            return Response(
                message="Error: 'referrer_id' and 'new_agent_email' are required.\n\n"
                        "Example: platapay_marketing action=referral referrer_id=AGT-001 "
                        "referrer_email=agent@example.com new_agent_email=newagent@example.com status=approved",
                break_loop=False
            )
        
        payload = {
            "referrer_id": referrer_id,
            "referrer_email": referrer_email,
            "referrer_name": referrer_name,
            "new_agent_email": new_agent_email,
            "new_agent_name": new_agent_name,
            "status": status
        }
        
        try:
            response = requests.post(
                self.webhooks["referral"],
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                rewards = result.get('rewards', {})
                
                reward_text = ""
                if rewards.get('referrerReward'):
                    reward_text += f"- Referrer reward: ₱{rewards['referrerReward']}\n"
                if rewards.get('newAgentBonus'):
                    reward_text += f"- New agent bonus: ₱{rewards['newAgentBonus']}\n"
                if rewards.get('milestoneBonus'):
                    reward_text += f"- 🏆 Milestone bonus: ₱{rewards['milestoneBonus']}\n"
                
                return Response(
                    message=f"""✅ **Referral Processed!**

**Referral Details:**
- Referrer: {referrer_id} ({referrer_email or 'N/A'})
- New Agent: {new_agent_email}
- Status: {status.upper()}

**Rewards:**
{reward_text or 'Pending approval'}

{result.get('milestoneMessage', '')}
{result.get('message', '')}""",
                    break_loop=False
                )
            else:
                return Response(
                    message=f"⚠️ Referral processing returned status {response.status_code}",
                    break_loop=False
                )
                
        except requests.exceptions.RequestException as e:
            return Response(
                message=f"⚠️ Could not reach n8n workflow: {str(e)}",
                break_loop=False
            )

    async def _trigger_social_post(self) -> Response:
        """Trigger a social media post."""
        platform = self.args.get("platform", "facebook")
        category = self.args.get("category", "")  # recruitment, features, tips, promos
        custom_text = self.args.get("text", "")
        
        payload = {
            "platform": platform,
            "category": category,
            "custom_text": custom_text
        }
        
        try:
            response = requests.post(
                self.webhooks["social_post"],
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return Response(
                    message=f"""✅ **Social Media Post Triggered!**

**Platform:** {result.get('platform', platform).title()}
**Category:** {result.get('category', 'auto-selected').title()}
**Status:** {result.get('status', 'queued').title()}

**Preview:**
{result.get('messagePreview', 'Content selected from library')}

{result.get('message', '')}""",
                    break_loop=False
                )
            else:
                return Response(
                    message=f"⚠️ Social post trigger returned status {response.status_code}",
                    break_loop=False
                )
                
        except requests.exceptions.RequestException as e:
            return Response(
                message=f"⚠️ Could not reach n8n workflow: {str(e)}",
                break_loop=False
            )

    async def _check_status(self) -> Response:
        """Check status of marketing workflows."""
        try:
            headers = {
                "X-N8N-API-KEY": self.n8n_api_key,
                "Content-Type": "application/json"
            }
            
            # Get recent executions
            response = requests.get(
                f"{self.n8n_base_url}/api/v1/executions?limit=10",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                executions = data.get('data', [])
                
                # Filter for PlataPay workflows
                platapay_executions = [
                    e for e in executions 
                    if 'platapay' in e.get('workflowId', '').lower() or 
                       'platapay' in str(e.get('workflowData', {}).get('name', '')).lower()
                ][:5]
                
                if not platapay_executions:
                    return Response(
                        message="📊 **Marketing Campaign Status**\n\nNo recent PlataPay marketing executions found.",
                        break_loop=False
                    )
                
                status_text = "📊 **Recent Marketing Campaign Executions:**\n\n"
                for ex in platapay_executions:
                    status_icon = "✅" if ex.get('finished') else "⏳" if not ex.get('stoppedAt') else "❌"
                    status_text += f"{status_icon} {ex.get('id', 'N/A')[:8]}... - {ex.get('startedAt', 'N/A')[:10]}\n"
                
                return Response(message=status_text, break_loop=False)
            else:
                return Response(
                    message="⚠️ Could not fetch execution status. Check n8n API key.",
                    break_loop=False
                )
                
        except Exception as e:
            return Response(
                message=f"Error checking status: {str(e)}",
                break_loop=False
            )

    async def _show_help(self) -> Response:
        """Show help for marketing tool."""
        return Response(
            message="""📢 **PlataPay Marketing Automation**

**Available Actions:**

1️⃣ **Agent Welcome Sequence**
```
platapay_marketing action=agent_welcome
  email=agent@example.com
  name="Juan Dela Cruz"
  phone=09171234567
  city=Manila
  referred_by=AGT-001
```

2️⃣ **Referral Processing**
```
platapay_marketing action=referral
  referrer_id=AGT-001
  referrer_email=agent@example.com
  new_agent_email=newagent@example.com
  status=approved
```
Status options: `pending`, `approved`, `first_transaction`

3️⃣ **Social Media Post**
```
platapay_marketing action=social_post
  platform=facebook
  category=recruitment
```
Categories: `recruitment`, `features`, `tips`, `promos`
Platforms: `facebook`, `twitter`, `instagram`

4️⃣ **Check Campaign Status**
```
platapay_marketing action=status
```

**Reward Structure:**
- Agent referral (approved): ₱500
- New agent bonus: ₱200
- First transaction bonus: ₱100
- 5 referrals milestone: ₱1,000
- 10 referrals milestone: ₱2,500
- 25 referrals milestone: ₱7,500
- 50 referrals milestone: ₱20,000""",
            break_loop=False
        )
