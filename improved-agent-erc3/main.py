import textwrap
from openai import OpenAI
from enhanced_agent import run_agent
from erc3 import ERC3

client = OpenAI()
core = ERC3()
MODEL_ID = "gpt-4o"

# Start session with metadata
res = core.start_session(
    benchmark="erc3-dev",
    workspace="my",
    name=f"Enhanced SGR Agent v2 ({MODEL_ID}) - Wiki + Security",
    architecture="Enhanced NextStep SGR with Wiki integration, robust security checks, and error handling")

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
        run_agent(MODEL_ID, core, task)
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
