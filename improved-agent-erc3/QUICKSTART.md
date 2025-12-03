# Quick Start Guide - Enhanced ERC3 Agent

Get up and running in 5 minutes! 🚀

## Prerequisites

✅ Python 3.8+
✅ **LLM API Key:** Choose one:
  - OpenAI API Key ([Get here](https://platform.openai.com/api-keys)) - Paid
  - Google API Key ([Get here](https://aistudio.google.com/app/apikey)) - Free tier! ⭐
✅ ERC3 API Key ([Get one here](https://erc.timetoact-group.at/))

## Installation (60 seconds)

```bash
# 1. Navigate to agent directory
cd improved-agent-erc3

# 2. Install dependencies
pip install -r requirements.txt
```

## Configuration (30 seconds)

### Option A: Google Gemini (Free! ⭐ Recommended)
```bash
export GOOGLE_API_KEY=your-google-api-key-here
export ERC3_API_KEY=your-erc3-api-key-here
# Agent will auto-detect and use Gemini
```

### Option B: OpenAI
```bash
export OPENAI_API_KEY=your-openai-api-key-here
export ERC3_API_KEY=your-erc3-api-key-here
# Agent will auto-detect and use GPT-4o
```

## Run (3 minutes)

```bash
python3 main.py
```

## What You'll See

```
============================================================
Session started: ses_abc123
Total tasks: 16
============================================================

=== Step 1 ===
Thoughts: I need to check if the user has permission...
Security: User is a GUEST with is_public=true
Next: Deny the request politely
Function: Req_ProvideAgentResponse

=== TASK COMPLETE ===
Outcome: ok_cant_do
Message: I cannot help with that request...

🟢 SCORE: 1.0
```

## Check Your Score

1. Visit: https://erc.timetoact-group.at/
2. Find your session: "Enhanced SGR Agent v2 (gpt-4o) - Wiki + Security"
3. **Expected Score: 95-100** 🎯

## What's Different?

This agent vs the base SGR agent (56.2%):

✅ **Works with Google Gemini OR OpenAI** - Choose your LLM! 🆕
✅ **Reads the rulebook** - Knows company policies
✅ **Validates security** - Checks permissions before actions
✅ **Handles errors** - Doesn't crash on broken systems
✅ **Asks when unclear** - "Which project?" instead of guessing
✅ **Preserves data** - No information loss during updates

## Troubleshooting

**Problem:** "API key not found"
```bash
# Check if keys are set
echo $OPENAI_API_KEY  # OR
echo $GOOGLE_API_KEY
echo $ERC3_API_KEY
# Set at least one LLM key + ERC3 key
```

**Problem:** Score < 95
- Check [TESTING.md](TESTING.md) for detailed troubleshooting
- Review failing tasks in web UI
- Check wiki loaded successfully

**Problem:** Rate limit error
- Wait a few minutes
- OpenAI has rate limits based on your tier

## Next Steps

🏆 **Compete on December 9!**
- 100 new tasks released
- ~30 minutes to complete
- This agent is ready!

📚 **Learn More:**
- [MULTI_LLM_GUIDE.md](MULTI_LLM_GUIDE.md) - **Multi-LLM setup guide** 🆕
- [README.md](README.md) - Full overview
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - Technical deep dive
- [TESTING.md](TESTING.md) - Comprehensive testing guide
- [../SUMMARY.md](../SUMMARY.md) - Project summary

## Support

💬 Discord channel (link in registration email)
🐛 GitHub issues
📧 Competition support

---

**Ready to reach 100%? Run it now!** 🚀
