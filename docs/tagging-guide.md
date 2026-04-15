# Langfuse Tagging Guide

temporal-lens correlates Langfuse LLM traces to Temporal activities using tags.
Without these tags, LLM spans appear as **orphaned nodes** attached directly to
the workflow root rather than beneath their parent activity.

---

## Required tags

When calling an LLM inside a Temporal activity, tag your Langfuse trace with:

| Tag | Value | Required |
|---|---|---|
| `temporal_workflow_id:<value>` | The running workflow's ID | **Yes** |
| `temporal_activity_id:<value>` | The activity's ID | **Yes** |
| `temporal_activity_type:<value>` | The activity's type name | Recommended |

---

## Python example (temporalio + langfuse SDK)

```python
import langfuse
from temporalio import activity

lf = langfuse.Langfuse()

@activity.defn
async def summarize_document(doc_id: str) -> str:
    info = activity.info()

    # Create a Langfuse trace tagged with Temporal context
    trace = lf.trace(
        name="summarize-document",
        tags=[
            f"temporal_workflow_id:{info.workflow_id}",
            f"temporal_activity_id:{info.activity_id}",
            f"temporal_activity_type:{info.activity_type}",
        ],
    )

    generation = trace.generation(
        name="gpt-4o-summarize",
        model="gpt-4o",
        input={"prompt": f"Summarize document {doc_id}"},
    )

    # ... call your LLM ...
    result = await call_openai(doc_id)

    generation.end(
        output=result,
        usage={"input": 512, "output": 128},
    )
    lf.flush()
    return result
```

---

## Using the Langfuse `@observe` decorator

If you use the `@observe` decorator, set tags on the current trace:

```python
from langfuse.decorators import langfuse_context, observe
from temporalio import activity

@observe(name="call-llm")
@activity.defn
async def call_llm_activity(prompt: str) -> str:
    info = activity.info()
    langfuse_context.update_current_trace(
        tags=[
            f"temporal_workflow_id:{info.workflow_id}",
            f"temporal_activity_id:{info.activity_id}",
            f"temporal_activity_type:{info.activity_type}",
        ]
    )
    # ... call LLM ...
```

---

## Verifying tags in Langfuse

1. Open your Langfuse project.
2. Navigate to **Traces**.
3. Find a recent trace and check the **Tags** column.
4. You should see `temporal_workflow_id:<id>`, `temporal_activity_id:<id>`.

If the tags are present, temporal-lens will automatically correlate the LLM
span as a child node of the matching Temporal activity.

---

## What happens without tags

Without `temporal_activity_id` tags, temporal-lens still shows LLM spans —
they just appear as children of the workflow root node rather than nested under
their parent activity. Add the tags to get the full, correlated DAG.
