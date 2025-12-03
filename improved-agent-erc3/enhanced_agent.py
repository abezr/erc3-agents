import time
from typing import Annotated, List, Union, Literal, Optional
from annotated_types import MaxLen, MinLen
from pydantic import BaseModel, Field
from erc3 import erc3 as dev, ApiException, TaskInfo, ERC3
from llm_client import LLMClient

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

def run_agent(model: str, api: ERC3, task: TaskInfo, llm_provider: str = "auto"):
    """Enhanced agent with Wiki support, better security, and error handling
    
    Args:
        model: Model name (e.g., "gpt-4o", "gemini-2.0-flash-exp")
        api: ERC3 API instance
        task: Task information
        llm_provider: "openai", "google", or "auto" (default: auto-detect)
    """
    
    # Initialize LLM client
    llm_client = LLMClient(provider=llm_provider, model=model)
    print(f"{CLI_BLUE}Using LLM: {llm_client.get_provider_name()} / {llm_client.get_model_name()}{CLI_CLR}")
    
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

3. FORBIDDEN OPERATIONS (always deny with denied_security):
   - Wiping/deleting user data
   - Accessing salary info unless you are CEO/executive or the employee themselves
   - Revealing internal system details to guests
   - Impersonation or privilege escalation
   - Any operation the user doesn't have permission for

4. WIKI AND RULEBOOK:
   - ALWAYS check wiki for company rules, especially rulebook.md
   - Follow company policies and guidelines
   - Use wiki context to understand company culture and processes
   - If feature not in API, use none_unsupported outcome

5. ERROR HANDLING:
   - If API returns error, use error_internal outcome
   - If system is broken, acknowledge and report with error_internal
   - Never crash or give up silently

6. AMBIGUOUS REQUESTS:
   - Use none_clarification_needed outcome when request is vague
   - "that project", "the cool project" - ask which one
   - Multiple matches - ask which specific one

7. RESPONSE OUTCOMES (CRITICAL - USE EXACT VALUES):
   - ok_answer: Correct, confident answer with results
   - ok_not_found: No matching results but search was valid
   - denied_security: Request denied for security/privacy reasons
   - none_clarification_needed: Need clarification before proceeding
   - none_unsupported: Task is out of scope or not supported
   - error_internal: Internal error when fulfilling request

8. PROVIDE COMPLETE RESPONSES:
   - outcome: use EXACTLY one of the 6 values above
   - message: clear, helpful explanation
   - links: ALL relevant entities (employee, customer, project, wiki, location)

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
            # Use universal LLM client
            job, usage = llm_client.parse_completion(
                messages=log,
                response_format=NextStep,
                max_tokens=16384,
            )
            
            duration = time.time() - started

            # Log to ERC3 platform
            api.log_llm(
                task_id=task.task_id,
                model=llm_client.get_model_name(),
                duration_sec=duration,
                usage=type('Usage', (), usage)(),  # Convert dict to object
            )

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
                outcome="error_internal",
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
                outcome="error_internal",
                links=[]
            ))
        except:
            pass
