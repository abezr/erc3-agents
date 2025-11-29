# Testing Guide for Enhanced ERC3 Agent

## Prerequisites

1. **Get your ERC3 API Key:**
   - Visit https://erc.timetoact-group.at/
   - Enter your registration email
   - Copy your API key

2. **Get OpenAI API Key:**
   - Visit https://platform.openai.com/api-keys
   - Create a new API key
   - Copy the key

## Setup

```bash
# Navigate to the agent directory
cd improved-agent-erc3

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=your-openai-key
export ERC3_API_KEY=your-erc3-key
```

## Running the Agent

```bash
python3 main.py
```

## What to Watch For

### 1. Wiki Loading
At the start, you should see:
```
Loading Wiki pages...
Found rulebook: rulebook.md
```

✅ **Success:** All wiki pages loaded
❌ **Failure:** "Could not load wiki" - check API permissions

### 2. Security Checks
For each step, watch the console output:
```
=== Step 1 ===
Thoughts: I need to check if the user has permission...
Security: User is a GUEST with is_public=true, can only get date
Next: Deny the request politely
Function: Req_ProvideAgentResponse
```

✅ **Success:** Security field shows explicit validation
❌ **Failure:** Security check missing or vague

### 3. Error Handling
If a task has broken API:
```
✗ API ERROR: Internal Server Error
  Details: System unavailable
```

✅ **Success:** Agent continues, provides error response
❌ **Failure:** Agent crashes or stops

### 4. Task Completion
At end of each task:
```
=== TASK COMPLETE ===
Outcome: ok_answer
Message: Here is the information you requested...
Links:
  - employee: helene_stutz
  - project: proj_acme_line3_cv_poc

🟢 SCORE: 1.0
```

✅ **Success:** Green circle (🟢) with score 1.0
🟡 **Partial:** Yellow circle (🟡) with score 0.5
❌ **Failure:** Red circle (🔴) with score 0.0

## Expected Results

### Session Summary
After all tasks complete:
```
SESSION COMPLETE!
View results at: https://erc.timetoact-group.at/
```

### Web UI
1. Visit https://erc.timetoact-group.at/
2. View leaderboard
3. Find your session: "Enhanced SGR Agent v2 (gpt-4o) - Wiki + Security"
4. **Expected Score: 95-100**

## Troubleshooting

### Score < 95

1. **Check Web UI for failing tasks:**
   - Click on your session
   - Review individual task scores
   - Read evaluation logs

2. **Common Issues:**

   **Security tests failing:**
   - Verify wiki loaded correctly
   - Check security_check field shows explicit validation
   - Ensure system prompt includes CRITICAL SECURITY RULES

   **Ambiguity tests failing:**
   - Check agent asks for clarification on vague requests
   - Verify "which project?" type responses

   **Update tests failing:**
   - Ensure agent gets current record before updating
   - Verify all fields preserved during update

3. **Debug Mode:**
   
   Add more verbose logging:
   ```python
   # In enhanced_agent.py, add after line 150:
   print(f"FULL JOB: {job.model_dump_json(indent=2)}")
   ```

### Common Errors

**"API key not found"**
```bash
# Check environment variables
echo $ERC3_API_KEY
echo $OPENAI_API_KEY

# Re-export if needed
export ERC3_API_KEY=your-key
export OPENAI_API_KEY=your-key
```

**"Rate limit exceeded"**
- Wait a few minutes
- OpenAI API has rate limits
- Consider upgrading OpenAI tier

**"Max iterations reached"**
- Task is very complex
- Agent hit 25-step limit
- Review task logs to see where it got stuck

## Iterative Improvement

If score < 100:

1. **Identify failing tasks** in web UI
2. **Analyze failure reasons** in evaluation logs
3. **Enhance system prompt** with more specific rules
4. **Re-run:** `python3 main.py`
5. **Repeat** until 100% achieved

## Performance Monitoring

Track these metrics:
- **Total Score:** Should be ≥ 95
- **Security Tests:** Should be 100% (critical)
- **Error Handling:** Should pass broken_system test
- **Permission Tests:** Should distinguish guest/member/lead/executive
- **Response Quality:** Should include outcome + message + links

## Success Criteria

✅ **Perfect Run:**
- All tasks show 🟢 (score 1.0)
- Total score: 100
- No crashes or exceptions
- All security tests passed
- Rulebook compliance 100%

🎯 **Target: 100/100 on ERC3-dev benchmark**

## Next Steps After Testing

1. **Review Leaderboard Position**
   - Compare with other agents
   - Note architecture (should show Enhanced SGR)

2. **Prepare for Competition**
   - Competition on December 9
   - 100 new tasks released
   - ~30 minutes to complete
   - Same API, different tasks

3. **Practice Switching Benchmarks**
   - If ERC3-TEST becomes available
   - Practice quick switching
   - Ensure agent works on new tasks

## Support

Issues? Questions?
- Discord channel (link in registration email)
- GitHub issues: https://github.com/trustbit/erc3-agents
- Competition page: https://www.timetoact-group.at/events/enterprise-rag-challenge-part-3
