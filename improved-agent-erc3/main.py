import os
import textwrap
from enhanced_agent import run_agent
from erc3 import ERC3

# Configuration
# LLM Provider: "auto" (detect from env), "openai", or "google"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")

# Model selection based on provider
# OpenAI: "gpt-4o", "gpt-4o-mini", "gpt-4-turbo"
# Google: "gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"
MODEL_ID = os.getenv("MODEL_ID", None)  # None = use default for provider

# Auto-select model based on provider if not specified
if MODEL_ID is None:
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_google = bool(os.getenv("GOOGLE_API_KEY"))
    
    if LLM_PROVIDER == "google" or (LLM_PROVIDER == "auto" and has_google and not has_openai):
        MODEL_ID = "gemini-2.0-flash-exp"
        effective_provider = "google"
    else:
        MODEL_ID = "gpt-4o"
        effective_provider = "openai"
else:
    effective_provider = LLM_PROVIDER

print(f"🤖 LLM Configuration:")
print(f"   Provider: {effective_provider}")
print(f"   Model: {MODEL_ID}")
print()

core = ERC3()

# Start session with metadata
res = core.start_session(
    benchmark="erc3-dev",
    workspace="my",
    name=f"Enhanced SGR Agent v2.1 ({MODEL_ID}) - Multi-LLM",
    architecture=f"Enhanced NextStep SGR with {effective_provider.upper()} ({MODEL_ID}), Wiki integration, security checks")

status = core.session_status(res.session_id)
print(f"\n{'='*60}")
print(f"Session started: {res.session_id}")
print(f"Total tasks: {len(status.tasks)}")
print(f"{'='*60}\n")

for idx, task in enumerate(status.tasks, 1):
    print("\n" + "="*60)
    print(f"TASK {idx}/{len(status.tasks)}: {task.spec_id}")
    print(f"ID: {task.task_id}")
    print(f"Text: {task.task_text}")
    print("="*60)
    
    # Start the task
    core.start_task(task)
    
    try:
        run_agent(MODEL_ID, core, task, llm_provider=LLM_PROVIDER)
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    # Complete and get result
    result = core.complete_task(task)
    
    if result.eval:
        explain = textwrap.indent(result.eval.logs, "  ")
        score_color = "🟢" if result.eval.score == 1.0 else "🔴" if result.eval.score == 0 else "🟡"
        print(f"\n{score_color} SCORE: {result.eval.score}")
        print(f"EVALUATION:\n{explain}\n")
    
    print(f"Completed {idx}/{len(status.tasks)} tasks\n")

# Submit session
core.submit_session(res.session_id)

print("\n" + "="*60)
print("SESSION COMPLETE!")
print("="*60)
print(f"\nView results at: https://erc.timetoact-group.at/")
