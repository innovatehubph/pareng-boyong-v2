#!/bin/bash
# =============================================================================
# VPS SSH Setup & Verification
# Run this to ensure SSH access from Docker to VPS is working
# =============================================================================

echo "🔧 VPS SSH Setup & Verification"
echo "================================"

VPS_HOST="172.27.0.1"
SSH_KEY="/root/.ssh/id_ed25519_boyong"
VPS_AUTH="/vps/root/.ssh/authorized_keys"

# Step 1: Check SSH client
echo -n "[1/5] SSH client... "
if which ssh > /dev/null 2>&1; then
    echo "✅ Available"
else
    echo "❌ Not found! Installing..."
    apt-get update -qq && apt-get install -y -qq openssh-client
fi

# Step 2: Check/create SSH key
echo -n "[2/5] SSH key... "
if [ -f "$SSH_KEY" ]; then
    echo "✅ Exists ($SSH_KEY)"
else
    echo "⚠️ Missing. Generating..."
    ssh-keygen -t ed25519 -f "$SSH_KEY" -N "" -C "boyong-vps-access"
    echo "✅ Generated"
fi

# Step 3: Get public key
PUB_KEY=$(ssh-keygen -y -f "$SSH_KEY" 2>/dev/null)
echo -n "[3/5] Public key... "
if [ -n "$PUB_KEY" ]; then
    echo "✅ Derived"
else
    echo "❌ Could not derive public key!"
    exit 1
fi

# Step 4: Check/add to authorized_keys
echo -n "[4/5] VPS authorized_keys... "
if grep -q "boyong-vps-access" "$VPS_AUTH" 2>/dev/null; then
    echo "✅ Key already authorized"
else
    echo "$PUB_KEY boyong-vps-access" >> "$VPS_AUTH"
    echo "✅ Key added to authorized_keys"
fi

# Step 5: Test SSH connection
echo -n "[5/5] SSH connection test... "
RESULT=$(ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -o LogLevel=ERROR     -i "$SSH_KEY" root@"$VPS_HOST" "echo SSH_OK" 2>&1)
if echo "$RESULT" | grep -q "SSH_OK"; then
    echo "✅ Connected to VPS!"
else
    echo "❌ Connection failed: $RESULT"

    # Try alternate IPs
    for ip in 172.17.0.1 172.18.0.1; do
        echo -n "    Trying $ip... "
        RESULT=$(ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o BatchMode=yes             -i "$SSH_KEY" root@$ip "echo SSH_OK" 2>&1)
        if echo "$RESULT" | grep -q "SSH_OK"; then
            echo "✅ Works! Updating VPS_HOST to $ip"
            sed -i "s/VPS_HOST=.*/VPS_HOST="$ip"/" /root/vps-ssh.sh 2>/dev/null
            sed -i "s/VPS_HOST=.*/VPS_HOST="$ip"/" /a0/skills/vps-ssh/scripts/vps-ssh.sh 2>/dev/null
            VPS_HOST=$ip
            break
        else
            echo "❌"
        fi
    done
fi

# Install helper to /root
cp /a0/skills/vps-ssh/scripts/vps-ssh.sh /root/vps-ssh.sh
chmod +x /root/vps-ssh.sh

echo ""
echo "================================"
echo "✅ Setup complete!"
echo "Usage: /root/vps-ssh.sh 'your command here'"
echo "VPS Host: $VPS_HOST"
echo "SSH Key: $SSH_KEY"
