#!/bin/bash

# Multi-Bitaxe Monitor Update Script

echo "🔄 Multi-Bitaxe Monitor Update"
echo "=============================="

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not a git repository. Please run from the project directory."
    exit 1
fi

# Backup current config if it exists
if [ -f "config.json" ]; then
    echo "💾 Backing up current configuration..."
    cp config.json config.json.backup
    echo "✅ Configuration backed up to config.json.backup"
fi

# Pull latest changes
echo "📥 Pulling latest changes..."
if git pull origin main; then
    echo "✅ Successfully updated to latest version"
else
    echo "❌ Failed to pull updates. Please check your git status."
    exit 1
fi

# Update dependencies
echo "📦 Updating dependencies..."
if pip3 install -r requirements.txt --upgrade; then
    echo "✅ Dependencies updated successfully"
else
    echo "⚠️  Failed to update some dependencies"
fi

# Restore config if backup exists
if [ -f "config.json.backup" ]; then
    echo "🔧 Restoring configuration..."
    if [ -f "config.json" ]; then
        echo "💡 New config.json found. Your old config is saved as config.json.backup"
        echo "💡 Please review and merge any new settings manually."
    else
        mv config.json.backup config.json
        echo "✅ Configuration restored"
    fi
fi

echo ""
echo "🎉 Update complete!"
echo ""
echo "Changes in this update:"
git log --oneline -5
echo ""
echo "To see full changelog: cat CHANGELOG.md"