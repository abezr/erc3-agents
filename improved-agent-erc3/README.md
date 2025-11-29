# Enhanced ERC3 Agent v2.0 - Achieving 100% Score

This is an improved version of the SGR agent with enhancements to reach 100% score on the ERC3-dev benchmark.

**🎯 Version 2.0:** Now using correct outcome enum values based on [@timurkhakhalev's documentation](https://github.com/timurkhakhalev/erc3) from ERC3 SDK v1.0.7 - the same documentation that enabled achieving 100% score!

## Key Improvements

### 🆕 Version 2.0 Critical Fix
- **Correct Outcome Enum Values** - Now using exact values from SDK v1.0.7:
  - ✅ `ok_answer` - Success with results
  - ✅ `ok_not_found` - No results (valid search)  
  - ✅ `denied_security` - Permission denied (was: `ok_cant_do`)
  - ✅ `none_clarification_needed` - Need clarification (NEW)
  - ✅ `none_unsupported` - Not implemented (NEW)
  - ✅ `error_internal` - System error (was: `error`)

See [OUTCOME_GUIDE.md](OUTCOME_GUIDE.md) for detailed examples and [CHANGELOG.md](CHANGELOG.md) for migration notes.

### 1. **Wiki and Rulebook Integration**
- Automatically loads all wiki pages at the start of each task
- Includes rulebook.md and company policies in the system prompt
- Uses wiki context to understand company culture and processes

### 2. **Robust Security and Access Control**
- Explicit security checks in the reasoning loop
- Validates user permissions before any operation
- Handles different access levels:
  - **GUEST** (is_public=true): Only allowed to get today's date
  - **TEAM MEMBER**: Read-only access to their projects
  - **PROJECT LEAD**: Can update projects they lead
  - **EXECUTIVES**: Broad access including salary changes
- Prevents forbidden operations (data wiping, impersonation, unauthorized salary access)

### 3. **Better Error Handling**
- Graceful handling of API errors
- Resilient to broken systems
- Comprehensive try-catch blocks
- Clear error messages to users

### 4. **Improved Reasoning**
- Added "thoughts" field for detailed reasoning
- Added "security_check" field for explicit permission validation
- Better context awareness
- Handles ambiguous requests by asking for clarification

### 5. **Complete Responses**
- Always includes proper outcome (ok_answer, ok_cant_do, error)
- Clear, helpful messages
- Complete entity links (project, customer, employee IDs)

### 6. **Enhanced Update Operations**
- Gets full current record before updating
- Preserves ALL existing fields
- Validates permissions before any update
- Fills in missing fields to prevent data loss

## Installation

```bash
# Navigate to the agent directory
cd improved-agent-erc3

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Set environment variables
export OPENAI_API_KEY=your-openai-key
export ERC3_API_KEY=your-erc3-key

# Run the agent
python3 main.py
```

## Architecture

The agent uses an enhanced version of Schema-Guided Reasoning (SGR) with:

1. **Pre-flight Wiki Loading**: Loads all wiki content before starting reasoning
2. **Security-First Reasoning**: Explicit security validation in each step
3. **Extended Tool Set**: Includes wiki operations (list, load, search, update)
4. **Structured Output**: Uses Pydantic models with thoughts, security checks, and planning
5. **Iterative Refinement**: Up to 25 reasoning steps with full context preservation

## Scoring Strategy

This agent aims to achieve 100% by:

1. ✅ **Never violating security rules** - Strict access control prevents unauthorized operations
2. ✅ **Reading and following the rulebook** - Wiki integration ensures policy compliance
3. ✅ **Handling edge cases** - Robust error handling for broken systems, ambiguous requests
4. ✅ **Complete and accurate responses** - Always includes outcome, message, and links
5. ✅ **Permission validation** - Checks access before every sensitive operation
6. ✅ **Data integrity** - Preserves existing data during updates

## Comparison to Base Agent

| Feature | Base SGR Agent | Enhanced Agent |
|---------|---------------|----------------|
| Wiki Support | ❌ | ✅ Automatic loading |
| Security Checks | ⚠️ Basic | ✅ Explicit validation |
| Error Handling | ⚠️ Basic | ✅ Comprehensive |
| Access Control | ⚠️ Implicit | ✅ Explicit per-step |
| Ambiguity Handling | ❌ | ✅ Asks for clarification |
| Update Safety | ⚠️ Basic | ✅ Field preservation |
| Reasoning Visibility | ⚠️ Limited | ✅ Detailed thoughts |

## Expected Score

**Target: 100/100**

Based on the enhancements:
- Security tests: Should pass all guest/member/lead/executive access tests
- Rulebook tests: Should follow all company policies
- Error handling: Should gracefully handle broken systems
- Ambiguity: Should ask for clarification on vague requests
- Updates: Should preserve data integrity

## Notes

- Uses GPT-4o for best reasoning capabilities
- Max 25 reasoning steps per task (increased from 20)
- Color-coded console output for better debugging
- Detailed logging of thoughts, security checks, and actions
