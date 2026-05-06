# Argus: Agentic Code Reviewer Architecture

This document provides a comprehensive overview of the Argus project, detailing its purpose, advantages over standard LLMs, and the underlying architecture powering the code review pipeline.

---

## 1. What the Project Does

Argus is an **Agentic Code Reviewer**, a full-stack application (React frontend + FastAPI backend + Supabase) designed to provide high-quality, hallucination-free code reviews for Python. 

Instead of just sending code to an LLM and hoping for a good response, Argus uses an autonomous agent workflow. It combines **Static Analysis Tools**, **Retrieval-Augmented Memory (RAG)**, and an **LLM-as-a-Judge (Critic)** to provide intelligent, team-aware, and highly accurate code reviews.

## 2. How it is Better Than a Normal LLM

A standard LLM (like ChatGPT or Claude) given a prompt to "review this code" suffers from several critical flaws:
- **Hallucinations:** They frequently invent issues on line numbers that don't exist.
- **Triviality/Noise:** They often complain about subjective style choices or missing docstrings, cluttering the review.
- **Amnesia:** They cannot remember how a team previously resolved an issue, leading to repetitive and inconsistent feedback.
- **Lack of Ground Truth:** They guess at cyclomatic complexity or syntax errors instead of actually measuring them.

**Argus solves this by:**
- Giving the LLM access to actual static analysis tools (`flake8`, `radon`, `ast`) to get factual ground truth before commenting.
- Passing all generated comments through a strict **Critique Agent** that rejects useless or hallucinated feedback.
- Using a local **Vector Database (ChromaDB)** to remember past approved comments, ensuring the system "learns" a team's preferences over time without needing to be retrained.

## 3. How RL (Reinforcement Learning) is Used

*Note: The codebase **does not** use Reinforcement Learning (like PPO or RLHF) in the traditional sense.* 

Instead of mathematically updating neural network weights (which is expensive and slow), Argus simulates "learning from feedback" using **Retrieval-Augmented Generation (RAG)**. 

When a high-confidence comment is approved, it is stored in ChromaDB as a vector embedding. The next time similar code is reviewed, Argus retrieves these past decisions and injects them into the prompt (e.g., `"PAST REVIEW DECISIONS: Do not flag missing type hints on internal utility functions"`). This achieves the primary goal of RLHF (aligning with user preferences) instantly and at zero training cost.

## 4. How ReAct (Reasoning and Acting) is Used

The core of the system is powered by a **ReAct Agent** (implemented via `langgraph`/`langchain`). ReAct allows the LLM to loop between *Reasoning* about the task and *Acting* by using external tools.

When the agent receives the code, the loop looks like this:
1. **Thought:** "I need to check if there are any syntax or styling errors."
2. **Action:** Call the `flake8` tool on the provided code.
3. **Observation:** The tool returns `Line 12: F401 'os' imported but unused`.
4. **Thought:** "The code is also quite nested, I should check complexity."
5. **Action:** Call the `radon` tool.
6. **Final Output:** The agent writes the final review incorporating the factual data it retrieved.

## 5. How the Critique Agent is Used

LLMs, even when using tools, can still be overly eager to point out trivial issues. Argus implements a **Critic layer** (an LLM-as-a-Judge) to filter the output.

After the ReAct agent generates its raw review, the text is parsed into individual JSON objects (Line, Comment, Severity, Confidence). 

Each comment is then sent independently to the **Critic Chain** (`core/critic.py`). The critic asks four strict questions:
1. Is the line number plausible?
2. Is the comment actually relevant?
3. Is it a real issue and not just noise?
4. Is the confidence score justified?

If the critic approves, it outputs `{"approved": true}` and adjusts the confidence. If it rejects the comment, it is completely hidden from the user, ensuring a high signal-to-noise ratio.

## 6. Entire Pipeline & Model Architecture

The backend utilizes `Llama-3.3-70B-Versatile` via the Groq API for ultra-fast inference, and a local `all-MiniLM-L6-v2` SentenceTransformer for zero-cost memory embeddings.

### The Pipeline (Config C - Full Pipeline)

1. **User Submission:** The frontend sends a Python code snippet and a `team_id` to the FastAPI backend.
2. **Memory Retrieval (RAG):** The backend queries the local ChromaDB for the `team_id` to find past review decisions on structurally similar code.
3. **Prompt Construction:** The retrieved memories and the new code are combined into the system prompt.
4. **Agent Invocation (ReAct):** The Groq LLaMA model processes the prompt, uses tools (`flake8`, `radon`, `ast`) to inspect the code, and generates a raw text review.
5. **Parsing:** A secondary LLM call formats the raw text into a structured list of JSON `ReviewComment` objects.
6. **Critique / Verification:** Every single parsed comment is evaluated by the Critic LLM.
7. **Storage:** Surviving comments with a confidence score above a set threshold (e.g., `0.8`) are instantly embedded and saved to ChromaDB for future memory.
8. **Response:** The finalized, highly-vetted comments are returned to the React frontend to be displayed on the UI.
