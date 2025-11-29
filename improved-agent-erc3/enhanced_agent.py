import time
from typing import Annotated, List, Union, Literal, Optional
from annotated_types import MaxLen, MinLen
from pydantic import BaseModel, Field
from erc3 import erc3 as dev, ApiException, TaskInfo, ERC3
from openai import OpenAI

client = OpenAI()

class NextStep(BaseModel):
    thoughts: str = Field(..., description="Your detailed reasoning about the current situation")
    security_check: str = Field(..., description="Security and access level verification based on current user permissions")
    current_state: str
    plan_remaining_steps_brief: Annotated[List[str], MinLen(1), MaxLen(5)] = Field(..., description="explain your thoughts on how to accomplish - what steps to execute")
    task_completed: bool
    function: Union[
        dev.Req_ProvideAgentResponse,
        dev.Req_ListProjects,
        dev.Req_ListEmployees,
        dev.Req_ListCustomers,
        dev.Req_GetCustomer,
        dev.Req_GetEmployee,
        dev.Req_GetProject,
        dev.Req_GetTimeEntry,
        dev.Req_SearchProjects,
        dev.Req_SearchEmployees,
        dev.Req_LogTimeEntry,
        dev.Req_SearchTimeEntries,
        dev.Req_SearchCustomers,
        dev.Req_UpdateTimeEntry,
        dev.Req_UpdateProjectTeam,
        dev.Req_UpdateProjectStatus,
        dev.Req_UpdateEmployeeInfo,
        dev.Req_TimeSummaryByProject,
        dev.Req_TimeSummaryByEmployee,
        dev.Req_ListWikiPages,
        dev.Req_LoadWikiPage,
        dev.Req_SearchWiki,
        dev.Req_UpdateWikiPage,
    ] = Field(..., description="execute first remaining step")


CLI_RED = "\x1B[31m"
CLI_GREEN = "\x1B[32m"
CLI_BLUE = "\x1B[34m"
CLI_YELLOW = "\x1B[33m"
CLI_CLR = "\x1B[0m"

def run_agent(model: str, api: ERC3, task: TaskInfo):
    """Enhanced agent with Wiki support, better security, and error handling"""
    
    store_api = api.get_erc_dev_client(task)
    about = store_api.who_am_i()
    
    # Load wiki pages to understand company rules and context
    wiki_content = {}
    try:
        wiki_list = store_api.list_wiki_pages()
        print(f"{CLI_YELLOW}Loading Wiki pages...{CLI_CLR}")
        
        # Load important pages, especially rulebook
        for path in wiki_list.paths:
            try:
                page = store_api.load_wiki_page(path)
                wiki_content[path] = page.content
                if 'rulebook' in path.lower() or 'rule' in path.lower():
                    print(f"{CLI_YELLOW}Found rulebook: {path}{CLI_CLR}")
            except Exception as e:
                print(f"{CLI_RED}Could not load {path}: {e}{CLI_CLR}")
    except Exception as e:
        print(f"{CLI_RED}Could not load wiki: {e}{CLI_CLR}")

    # Build comprehensive system prompt with wiki knowledge
    system_prompt = f"""
You are a business assistant helping customers of Aetherion Analytics GmbH.

CRITICAL SECURITY RULES - ENFORCE STRICTLY:

1. ACCESS LEVELS (check who_am_i response):
   - GUEST (is_public=true, no current_user): Can ONLY get today's date. Deny ALL other requests politely.
   - TEAM MEMBER: Can READ projects they are team member of. Cannot write/update.
   - PROJECT LEAD: Can READ and WRITE for projects they lead. Can change project status, update team.
   - EXECUTIVES (CEO, CTO, etc.): Broad access including salary changes.
   - NO USER (threat): Deny immediately if trying to impersonate someone.

2. BEFORE ANY UPDATE OPERATION:
   - Verify user has permission (is project lead, is executive, etc.)
   - Get the full current record first
   - Preserve ALL existing fields when updating
   - Validate the operation is allowed

3. FORBIDDEN OPERATIONS (always deny):
   - Wiping/deleting user data
   - Accessing salary info unless you are CEO/executive or the employee themselves
   - Revealing internal system details to guests
   - Impersonation or privilege escalation
   - Operations not in the API (if feature not available, say so)

4. WIKI AND RULEBOOK:
   - ALWAYS check wiki for company rules, especially rulebook.md
   - Follow company policies and guidelines
   - Use wiki context to understand company culture and processes

5. ERROR HANDLING:
   - If API returns error, handle gracefully
   - If system is broken, acknowledge and report inability to complete
   - Never crash or give up silently

6. AMBIGUOUS REQUESTS:
   - Ask for clarification when request is vague
   - "that project", "the cool project" - ask which one
   - Multiple matches - ask which specific one

7. PROVIDE COMPLETE RESPONSES:
   - outcome: must be ok_answer, ok_cant_do, or error
   - message: clear, helpful explanation
   - links: ALL relevant entities (project, customer, employee IDs)

# Current user context:
{about.model_dump_json()}
"""

    # Add user info if available
    if about.current_user:
        try:
            usr = store_api.get_employee(about.current_user)
            system_prompt += f"\n# Current user details:\n{usr.model_dump_json()}"
        except:
            pass

    # Add wiki content to system prompt
    if wiki_content:
        system_prompt += "\n\n# COMPANY WIKI AND RULES:\n"
        for path, content in wiki_content.items():
            system_prompt += f"\n## {path}\n{content}\n"

    # Conversation log
    log = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task.task_text},
    ]

    # Reasoning loop with limit
    for i in range(25):
        step = f"step_{i + 1}"
        print(f"\n{CLI_BLUE}=== Step {i+1} ==={CLI_CLR}")
        
        started = time.time()

        try:
            completion = client.beta.chat.completions.parse(
                model=model,
                response_format=NextStep,
                messages=log,
                max_completion_tokens=16384,
            )

            api.log_llm(
                task_id=task.task_id,
                model=model,
                duration_sec=time.time() - started,
                usage=completion.usage,
            )

            job = completion.choices[0].message.parsed

            # Print reasoning
            print(f"{CLI_YELLOW}Thoughts:{CLI_CLR} {job.thoughts[:150]}...")
            print(f"{CLI_YELLOW}Security:{CLI_CLR} {job.security_check[:100]}...")
            print(f"{CLI_YELLOW}Next:{CLI_CLR} {job.plan_remaining_steps_brief[0]}")
            print(f"{CLI_YELLOW}Function:{CLI_CLR} {job.function.__class__.__name__}")

        except Exception as e:
            print(f"{CLI_RED}LLM Error: {e}{CLI_CLR}")
            # Try to respond with error
            store_api.dispatch(dev.Req_ProvideAgentResponse(
                message=f"I encountered an error processing your request: {str(e)}",
                outcome="error",
                links=[]
            ))
            break

        # Add to conversation history
        log.append({
            "role": "assistant",
            "content": f"{job.thoughts}\n\nNext step: {job.plan_remaining_steps_brief[0]}",
            "tool_calls": [{
                "type": "function",
                "id": step,
                "function": {
                    "name": job.function.__class__.__name__,
                    "arguments": job.function.model_dump_json(),
                }}]
        })

        # Execute the tool
        try:
            result = store_api.dispatch(job.function)
            txt = result.model_dump_json(exclude_none=True, exclude_unset=True)
            print(f"{CLI_GREEN}✓ SUCCESS:{CLI_CLR} {txt[:200]}...")
            
        except ApiException as e:
            txt = f"API Error: {e.api_error.error}\nDetails: {e.detail}"
            print(f"{CLI_RED}✗ API ERROR: {e.api_error.error}{CLI_CLR}")
            print(f"{CLI_RED}  Details: {e.detail}{CLI_CLR}")
            
        except Exception as e:
            txt = f"Unexpected error: {str(e)}"
            print(f"{CLI_RED}✗ ERROR: {e}{CLI_CLR}")

        # Check if task completed
        if isinstance(job.function, dev.Req_ProvideAgentResponse):
            print(f"\n{CLI_BLUE}=== TASK COMPLETE ==={CLI_CLR}")
            print(f"{CLI_GREEN}Outcome:{CLI_CLR} {job.function.outcome}")
            print(f"{CLI_GREEN}Message:{CLI_CLR} {job.function.message}")
            if job.function.links:
                print(f"{CLI_GREEN}Links:{CLI_CLR}")
                for link in job.function.links:
                    print(f"  - {link.kind}: {link.id}")
            break

        # Add result to conversation
        log.append({"role": "tool", "content": txt, "tool_call_id": step})

    else:
        # Hit max iterations
        print(f"{CLI_RED}Max iterations reached!{CLI_CLR}")
        try:
            store_api.dispatch(dev.Req_ProvideAgentResponse(
                message="I've reached my reasoning limit. Please try breaking this down into smaller requests.",
                outcome="error",
                links=[]
            ))
        except:
            pass
