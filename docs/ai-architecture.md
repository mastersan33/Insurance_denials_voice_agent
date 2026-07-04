# AI Architecture

## Overview

The voice agent is a **LangGraph state machine** that orchestrates a multi-turn conversation with insurance payer phone trees. It combines real-time speech (Twilio → ElevenLabs) with GPT-4o reasoning to navigate IVR menus, authenticate, gather claim information, and negotiate resolutions.

---

## State Machine

```
START
  │
  ▼
┌──────────┐     escalate?
│ planner  │──────────────────────────────────────┐
│          │                                       │
│ • Check  │  no escalate                         │
│   conf.  │──────────────┐                       │
│ • Check  │              │                       │
│   phase  │              ▼                       │
│   limits │         ┌──────────┐                 ▼
└──────────┘         │ executor │           ┌───────────┐
     ▲               │          │           │  ESCALATE │
     │               │ • LLM    │           │  (END)    │
     │               │   invoke │           └───────────┘
     │               │ • Tools  │
     │               └────┬─────┘
     │                    │
     │               ┌────▼─────┐     phase_complete?
     │               │ observer │──────────────────────►
     │               │          │                       │
     │               │ • Detect │  continue             │
     └───────────────│   phase  │◄──────────────────────┘
                     │   trans. │
                     └────┬─────┘
                          │ wrap_up_done?
                          ▼
                        END
```

### Node Descriptions

**planner** — Assesses current state before generating a response:
- Checks `confidence_score < threshold` → escalate
- Checks phase turn count > max turns → escalate
- Increments `phase_turn_count`

**executor** — Generates the agent's next utterance:
- Builds system prompt + phase-specific prompt
- Invokes GPT-4o with tool binding
- Returns response text + any tool calls

**observer** — Analyzes the response to detect transitions:
- `HUMAN_DETECTED` signal → advances from IVR to authentication
- `AUTH_COMPLETE` signal → advances to information_gathering
- `INFO_COMPLETE` → advances to negotiation
- `RESOLUTION_REACHED` → advances to wrap_up
- `ESCALATE` keyword → triggers human handoff

---

## Phases

| Phase | Goal | Max Turns |
|-------|------|-----------|
| `ivr_navigation` | Navigate phone tree to reach human rep | 20 |
| `authentication` | Provide provider credentials (NPI, tax ID) | 10 |
| `information_gathering` | Get claim status, denial reason, reference numbers | 30 |
| `negotiation` | Appeal denial, request reconsideration | 20 |
| `wrap_up` | Confirm action items, get reference numbers | 10 |

---

## Agent Tools

Tools are FastAPI-backed functions the LLM can call via function calling:

| Tool | Description |
|------|-------------|
| `get_billing_case_info` | Retrieve full case details (claim #, denial code, amounts) |
| `get_call_history` | Prior calls for this case |
| `update_call_outcome` | Record resolution/escalation in DB |
| `create_ticket` | Open a support ticket from within the call |
| `create_human_handoff` | Escalate to human agent |
| `record_phone_number` | Capture new payer contact discovered during call |
| `save_reference_number` | Store claim reference numbers |

---

## Prompts

Prompts are **externalized** in `agent/prompts.py` (not hardcoded inline in graph nodes).

System prompt components:
1. Role definition ("You are an expert medical billing specialist...")
2. Current case context (patient, payer, claim, denial)
3. Phase-specific instructions and signals
4. Tool usage guidelines
5. Communication constraints (professional, factual, never invent data)

**Hallucination prevention:**
- Agent only has access to data from the actual billing case
- Tools return real DB data — agent cannot fabricate claim numbers, amounts, dates
- Confidence score from STT — low confidence transcripts trigger clarification
- Phase-specific prompts constrain what information is relevant

---

## Memory Management

`agent/memory.py` manages `ConversationMemory` records:
- `key_facts`: dictionary of discovered information (reference #, rep name, etc.)
- `phase_history`: list of completed phases with outcomes
- `tool_results`: last N tool call results for context injection

Memory is loaded at the start of each turn and updated after each turn.

---

## Escalation Logic

`agent/escalation.py` triggers human handoff when:
1. `confidence_score < agent_config.confidence_threshold` (0.6)
2. Phase turn count exceeds maximum
3. LLM explicitly emits `ESCALATE` keyword
4. Call duration exceeds `max_call_duration_seconds` (1800s)
5. Repeated authentication failures (> 3)

On escalation:
- `HumanHandoff` record created with context summary
- Call session status updated to `transferred_to_human`
- Dashboard WebSocket pushes alert to operators

---

## AI Quality Considerations

| Risk | Mitigation |
|------|-----------|
| Hallucinated claim data | Agent reads from DB via tools only |
| Inappropriate language | Role-specific system prompt with strict constraints |
| Infinite loops | Phase turn limits + total call duration limit |
| Low-confidence STT | Confidence threshold check, clarification request |
| Failed tool calls | Try/except in tool handlers, graceful degradation |
| LLM latency | GPT-4o streaming; TTS starts as soon as first chunk arrives |

---

## Configuration

All agent parameters in `agent/config.py` — no magic numbers in graph logic:

```python
@dataclass
class AgentConfig:
    model: str                       # gpt-4o
    temperature: float               # 0.3 (low for factual task)
    max_tokens: int                  # 200 (concise responses)
    confidence_threshold: float      # 0.6 (escalate below this)
    max_call_duration_seconds: int   # 1800 (30 min hard limit)
    ivr_max_turns: int               # 20
    auth_max_turns: int              # 10
    gathering_max_turns: int         # 30
    negotiation_max_turns: int       # 20
    wrap_up_max_turns: int           # 10
```

---

## Latency Budget

| Component | Target P50 | Target P95 |
|-----------|-----------|-----------|
| STT (first word) | < 300ms | < 600ms |
| LLM response (streaming) | < 500ms | < 1500ms |
| TTS (first audio chunk) | < 200ms | < 400ms |
| End-to-end turn latency | < 1.5s | < 3s |

Audio is **streamed** at every stage — no buffering full audio before sending.
