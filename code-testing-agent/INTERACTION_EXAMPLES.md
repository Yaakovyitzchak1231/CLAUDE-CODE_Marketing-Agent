# Interactive Web Interface - Practical Examples

This guide shows real-world examples of interacting with the Code Testing Agent through the web interface.

## Example 1: Guided Code Audit

**Scenario**: You want to audit a specific part of the codebase, not everything.

```
# Start the agent with a broad task
Terminal: python agent.py --config configs/marketing-agent.yaml --web

# In browser at http://localhost:5000

Agent: "I'm starting a comprehensive audit. I'll map the entire project structure..."
Agent: "Found 150 files across 12 directories. Beginning analysis..."

[You realize this will take too long]

You: [Click ⏸️ Interrupt]
You: "Stop the full audit. Focus only on the authentication module in auth/"

Agent: "Understood. I'll focus on the authentication module."
Agent: "Analyzing auth/ directory..."
Agent: "Found authentication.py, jwt_handler.py, session.py"
Agent: "Testing for security vulnerabilities..."

[Wait for results]

Agent: "Found 2 security issues:
       1. JWT secret is hardcoded
       2. No rate limiting on login endpoint"

You: "Create a fix for the hardcoded JWT secret first"

Agent: "Creating fix for JWT secret..."
Agent: "I'll move it to environment variables and update config"
Agent: [Shows code changes]
Agent: "Should I create a PR?"

You: "Yes, create the PR with a detailed description"

Agent: "Creating pull request..."
Agent: "PR created: https://github.com/user/repo/pull/123"
```

**Result**: Instead of a 2-hour full audit, you got targeted results in 10 minutes.

## Example 2: Iterative Testing

**Scenario**: Test specific features and drill down based on findings.

```
You: "Test the API endpoints in the users module"

Agent: "Testing users module API endpoints..."
Agent: "Found 5 endpoints: create_user, get_user, update_user, delete_user, list_users"
Agent: "Running tests..."
Agent: "Test Results:
       - create_user: PASS
       - get_user: PASS
       - update_user: FAIL (returns 500 error)
       - delete_user: PASS
       - list_users: PASS"

You: "Investigate the update_user failure. What's causing the 500 error?"

Agent: "Analyzing update_user endpoint..."
Agent: "Found the issue: Missing validation for email field"
Agent: "When email is empty, database constraint fails causing 500"

You: "Show me the code"

Agent: [Shows update_user function]

You: "Create a fix that validates email before database update"

Agent: "Implementing email validation..."
Agent: [Shows fix]
Agent: "Running tests to verify fix..."
Agent: "Test now passes! Should I create a PR?"

You: "Yes, and add a test case for this scenario"

Agent: "Adding test case for empty email validation..."
Agent: "Creating PR with fix and test..."
Agent: "PR created successfully!"
```

**Result**: Found issue, created fix, added test, submitted PR - all through conversation.

## Example 3: Hallucination Detection Workflow

**Scenario**: Test if AI components are fabricating data.

```
You: "Test the research_agent for hallucinations. Check if citations are real."

Agent: "Starting hallucination detection for research_agent..."
Agent: "Found research_agent in langchain-service/agents/research.py"
Agent: "Testing with sample queries..."

Agent: "Test 1: 'Artificial intelligence history'
       Generated response includes citation: [Study from MIT, 2023]
       Verifying citation..."

You: "How are you verifying citations?"

Agent: "I'm checking if:
       1. The URL exists and is accessible
       2. The content matches the claim
       3. The date is accurate"

Agent: "Citation verification: URL returns 404 - HALLUCINATION DETECTED"

You: "Good catch! Are there more hallucinations?"

Agent: "Continuing tests..."
Agent: "Test 2: Statistics about AI adoption
       Claims '87% of companies use AI' - checking source..."
Agent: "Source found and verified - NO HALLUCINATION"

Agent: "Test 3: Future predictions
       Claims 'AI will achieve AGI by 2025' - no source cited
       This is speculation presented as fact - POTENTIAL HALLUCINATION"

You: "Create fixes for the confirmed hallucinations"

Agent: "I'll modify research_agent to:
       1. Validate URLs before citing
       2. Mark predictions as opinions
       3. Add source verification step"

You: "Show me the implementation plan first"

Agent: [Shows detailed plan]

You: "Looks good. Implement it and run tests"

Agent: "Implementing fixes..."
[Implementation progress...]
Agent: "Running tests with fixes..."
Agent: "All tests pass! Hallucinations eliminated."

You: "Create a PR with detailed description of what was fixed"

Agent: "Creating PR..."
```

**Result**: Systematic hallucination testing with iterative investigation and fixes.

## Example 4: Explaining Findings

**Scenario**: Agent finds issues and you want detailed explanations.

```
You: "Audit the database queries for performance issues"

Agent: "Auditing database queries..."
Agent: "Found 4 potential performance issues"

You: "Explain each issue in detail"

Agent: "Issue 1: N+1 Query in User Dashboard
       Location: dashboard.py:45
       Problem: Loading users then loading each user's posts in a loop
       Impact: 1 query + N queries instead of 2 queries
       Severity: HIGH (affects main dashboard)"

You: "Show me the problematic code"

Agent: [Shows code with N+1 pattern]

You: "What's the fix?"

Agent: "Use eager loading with join:
       users = User.query.options(joinedload(User.posts)).all()
       This reduces queries from N+1 to 2"

You: "Will this work with our pagination?"

Agent: "Good question. Let me check the pagination implementation..."
Agent: "Yes, but we need to modify the pagination to use subquery loading instead"
Agent: [Shows modified code]

You: "Perfect. Continue with the other issues"

Agent: "Issue 2: Missing Index on Foreign Key
       Location: posts table, user_id column
       Problem: Queries filtering by user_id do full table scan..."
```

**Result**: Deep dive into each issue with back-and-forth Q&A.

## Example 5: Multi-Stage Task

**Scenario**: Complex task broken into stages with review after each stage.

```
You: "I want to improve the test coverage of the API module. Do this in stages and wait for my approval after each stage."

Agent: "I'll break this into stages:
       Stage 1: Analyze current test coverage
       Stage 2: Identify gaps
       Stage 3: Prioritize missing tests
       Stage 4: Implement tests
       Stage 5: Verify coverage improvement

       Starting Stage 1: Analyzing current coverage..."

Agent: "Stage 1 Complete:
       - Current coverage: 45%
       - 12 files in API module
       - 48 functions total
       - 22 functions have tests
       - 26 functions untested

       Should I proceed to Stage 2?"

You: "Yes, identify the gaps"

Agent: "Stage 2: Identifying gaps..."
Agent: "Critical untested functions:
       1. authenticate_user() - NO TESTS
       2. validate_token() - NO TESTS
       3. refresh_token() - NO TESTS
       4. handle_payment() - NO TESTS
       ...

       Should I proceed to Stage 3: Prioritization?"

You: "Wait. The authentication functions are critical. Let's focus only on those. Skip the other stages and implement tests for authenticate_user, validate_token, and refresh_token."

Agent: "Understood. I'll implement tests for the 3 authentication functions."
Agent: "Implementing tests..."
[Shows test code being created]
Agent: "Running new tests..."
Agent: "All tests pass! Coverage increased from 45% to 62% for API module"

You: "Excellent. Create a PR"

Agent: "Creating PR..."
```

**Result**: Flexible workflow with user approval gates and course corrections.

## Example 6: Emergency Stop

**Scenario**: Agent is doing something wrong and needs immediate stopping.

```
Agent: "Analyzing all dependencies..."
Agent: "Found outdated package: requests 2.25.0"
Agent: "Updating to latest version..."
Agent: "Running pip install requests==2.31.0..."

[You realize this might break things]

You: [Click ⏹️ Stop]

[Agent stops immediately]

You: [In terminal, restart with different approach]

Terminal: python agent.py --config configs/marketing-agent.yaml --web --task "Check for outdated dependencies but DO NOT update them automatically"

Agent: "Checking for outdated dependencies without auto-update..."
Agent: "Found 5 outdated packages:
       - requests: 2.25.0 -> 2.31.0 (safe to update)
       - urllib3: 1.26.0 -> 2.0.0 (BREAKING CHANGES)
       ..."

You: "Update only the safe ones. Avoid urllib3."

Agent: "Updating safe packages only..."
```

**Result**: Prevented breaking changes by stopping agent at the right moment.

## Example 7: Real-Time Debugging

**Scenario**: Agent encounters errors and you debug together.

```
You: "Run the test suite"

Agent: "Running test suite..."
Agent: "Test failed: test_api_authentication"
Agent: "Error: KeyError: 'JWT_SECRET'"

You: "Check if JWT_SECRET is in the environment variables"

Agent: "Checking environment..."
Agent: "JWT_SECRET is not set in .env file"

You: "What does the authentication code expect?"

Agent: "Reading authentication.py..."
Agent: "Code expects: os.environ['JWT_SECRET']
       Falls back to: config.get('jwt.secret')
       Config value: None"

You: "Add JWT_SECRET to .env file with a test value"

Agent: "I cannot modify .env files for security reasons.
       However, I can create a .env.example with placeholder"

You: "Good idea. Create the .env.example and document this in README"

Agent: "Creating .env.example..."
Agent: "Adding documentation to README..."
Agent: "Done. Now tests should pass if user sets JWT_SECRET"

You: "Verify the tests pass with a test JWT_SECRET"

Agent: "Setting test JWT_SECRET temporarily..."
Agent: "Running tests again..."
Agent: "All tests pass!"
```

**Result**: Collaborative debugging session with agent.

## Tips for Effective Interaction

### 1. **Start Broad, Then Focus**
```
❌ "Check line 47 of auth.py"
✅ "Audit the authentication module" → then drill down based on findings
```

### 2. **Use Interrupt for Course Corrections**
```
Agent doing full audit → [Interrupt] → "Focus on auth module only"
```

### 3. **Ask for Explanations**
```
"Why did you choose this approach?"
"What are the tradeoffs?"
"Are there alternatives?"
```

### 4. **Break Complex Tasks into Steps**
```
"First, find the issue"
[Wait for results]
"Now explain the root cause"
[Wait for explanation]
"Now create a fix"
```

### 5. **Review Before Committing**
```
"Show me the fix first"
[Review code]
"Modify the fix to also handle edge case X"
[Review again]
"Looks good, create PR"
```

## Keyboard Shortcuts Reminder

- **Ctrl+Enter**: Send message
- **Tab**: Focus input
- **Escape**: (future) Clear input

## Next Steps

- Read INTERACTIVE_WEB_GUIDE.md for full feature documentation
- Read WEB_INTERFACE_GUIDE.md for setup and technical details
- Try the examples above with your own codebase
- Experiment with different interaction patterns

Happy interactive testing! 🚀
