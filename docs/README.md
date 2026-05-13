# Documentation Index

This folder contains operational documentation designed for both human reference and RAG (Retrieval-Augmented Generation) ingestion.

---

## Files Overview

### 1. **SOP_INVENTORY_RECONCILIATION.md**
- **Purpose:** Step-by-step operations manual for stock management
- **Audience:** Store staff, operations manager
- **Use Cases:**
  - How to add/remove stock
  - Handling negative stock emergencies
  - Daily and weekly reconciliation procedures
  - Escalation paths
- **RAG Integration:** Ingest sections 1-5 for operations Q&A
- **Example Queries RAG Can Answer:**
  - "How do I handle negative stock after a late sync?"
  - "What's the maximum I can add in one transaction?"
  - "When should I escalate to the manager?"

---

### 2. **ONBOARDING_GUIDE.md**
- **Purpose:** Day-by-day guide for new team members
- **Audience:** New hires, interns, retail staff
- **Use Cases:**
  - System access and dashboard orientation
  - First stock update walkthrough
  - Understanding customer segments
  - Using forecasts for reordering
  - Common tasks and shortcuts
- **RAG Integration:** Ingest for operational support copilot
- **Example Queries RAG Can Answer:**
  - "What are the three main dashboard pages?"
  - "How do I add stock using the API?"
  - "What does 'At Risk' customer segment mean?"

---

### 3. **TROUBLESHOOTING_GUIDES.md**
- **Purpose:** Diagnostic flowchart and fixes for common issues
- **Audience:** Operations staff, junior developers, support team
- **Use Cases:**
  - API connection problems
  - Database errors and recovery
  - UI/dashboard rendering issues
  - Forecast accuracy problems
  - Sync and integration issues
- **RAG Integration:** Best for "help, something broke" scenarios
- **Example Queries RAG Can Answer:**
  - "How do I fix 'Cannot connect to backend'?"
  - "What do I do if stock shows negative?"
  - "Why is the forecast so wrong?"

---

### 4. **INCIDENT_POSTMORTEM_TEMPLATE.md**
- **Purpose:** Template and completed examples for incident analysis
- **Audience:** Engineering team, operations leadership
- **Use Cases:**
  - Recording what went wrong after incidents
  - Capturing lessons learned
  - Tracking preventive actions
  - Building historical incident knowledge base
- **RAG Integration:** Ingest completed postmortems for "what happened before?" queries
- **Example Queries RAG Can Answer:**
  - "Have we had database lock issues before? What was the fix?"
  - "What was the root cause of the negative stock incident?"
  - "What preventive actions were taken after that outage?"

---

## How to Use for RAG

### Step 1: Load Documents into RAG System

```python
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import MarkdownHeaderTextSplitter

loader = DirectoryLoader(
    path="docs/",
    glob_pattern="*.md",
    loader_cls=TextLoader
)
docs = loader.load()

# Split by headers to preserve structure
splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("#", "Document"),
        ("##", "Section"),
        ("###", "Subsection")
    ]
)
split_docs = splitter.split_documents(docs)
```

### Step 2: Create Embeddings & Vector Store

```python
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

vectorstore = Chroma.from_documents(
    documents=split_docs,
    embedding=OpenAIEmbeddings(model="text-embedding-3-small")
)
```

### Step 3: Query Examples

```python
# Question from operations staff
query = "How do I handle negative stock after a late sync?"
results = vectorstore.similarity_search(query, k=5)
# Returns: sections from SOP_INVENTORY_RECONCILIATION.md section 2

# Question from new hire
query = "What does 'At Risk' customer segment mean?"
results = vectorstore.similarity_search(query, k=3)
# Returns: sections from ONBOARDING_GUIDE.md explaining segments

# Question during incident
query = "Database locked error, what do I do?"
results = vectorstore.similarity_search(query, k=5)
# Returns: debugging steps from TROUBLESHOOTING_GUIDES.md
```

---

## Integration with Current System

### Option 1: Add to Existing AI Assistant (Minimal Changes)
1. Create new agent: `agents/ops_help.py`
2. Route queries containing keywords like "help", "how", "SOP", "error"
3. Call RAG retriever before responding

### Option 2: Separate Copilot Page
1. Add "📚 Operations Help" page to Streamlit dashboard
2. Simple interface: text input + citation-based responses
3. No changes to existing agents/routes

### Option 3: Hybrid (Recommended)
1. Keep current agents for analytics/forecast/inventory math
2. Add RAG as a fallback for non-math queries
3. Upvote/downvote feedback to improve retrieval

---

## Document Maintenance

### Update Schedule
- **SOP_INVENTORY_RECONCILIATION.md:** Whenever process changes (monthly review)
- **ONBOARDING_GUIDE.md:** When new features added or UI changes
- **TROUBLESHOOTING_GUIDES.md:** Add new section whenever issue is resolved
- **INCIDENT_POSTMORTEM_TEMPLATE.md:** Fill out after each incident

### Versioning
Add to top of each file:
```
Version: 1.0
Last Updated: May 12, 2026
Next Review: June 12, 2026
Owner: [Name]
```

---

## Quality Checklist for RAG Ingestion

Before adding new documentation to RAG:
- [ ] Document has clear sections with headers
- [ ] Each section is self-contained (~200-400 words)
- [ ] Includes concrete examples (code snippets, commands, screenshots)
- [ ] References other docs where relevant
- [ ] No confidential information (passwords, API keys, PII)
- [ ] All external commands/URLs are tested and working
- [ ] Reviewed by domain expert (operations lead, dev lead)

---

## Example RAG Response Format

For the SOP assistant to follow:

```
User Query: "How do I handle negative stock after a late sync?"

RAG Response:
---
**Immediate Actions (Next 5 minutes):**
1. DO NOT accept new sales for this product
2. Check last sync timestamp...
[rest of response]

**Source:**
- Document: SOP_INVENTORY_RECONCILIATION.md
- Section: 2.2 Immediate Actions
- Version: 1.0
- Last Updated: May 12, 2026

**Confidence:** High (procedural SOP, not predictive)
**Requires Approval:** No
---
```

---

## Next Steps

1. ✅ Read these docs to understand your role/task
2. ✅ Bookmark for reference during work
3. ✅ When issues happen, search these docs first
4. ✅ Document the fix: help us improve the guides
5. ✅ Weekly: review "Troubleshooting" for recurring issues
