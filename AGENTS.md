# AGENTS.md — BotAutoCRM

> **The single source of truth for all AI Agents. You MUST read, understand, and strictly follow this workflow before writing any code.**

---

## 🚀 THE VIBE CODE + OUSTERHOUT WORKFLOW (5-STEP ENGINE)

### 1️⃣ Step 1: Align & Synchronize (Grill Me)
- **Input:** Start with a raw brief file (such as a JSON template, text requirements, or `clientbrief.mmd` Mermaid diagram).
- **Agent Action:** 
  * Read the input requirements and construct a mental "design tree".
  * Interview the User mercilessly by traversing the branches of the design tree. Ask at least 3-5 sharp, non-obvious questions.
  * *Goal:* Achieve a "shared understanding" between human and machine before writing a single line of code.

### 2️⃣ Step 2: Define the Destination (Write a PRD)
- **Agent Action:** Synthesize the shared understanding from Step 1 into a Product Requirement Document (PRD).
- **Ousterhout Integration:** Within the PRD, the Agent MUST explicitly define:
  * The problem statement and the simplest possible solution (Complexity Reduction).
  * Design of **Deep Modules**: Define clean, simple interfaces that hide significant implementation complexity underneath (Information Hiding).
  * Make interfaces somewhat general-purpose to facilitate future expansion and prevent "Class-itis".

### 3️⃣ Step 3: Map the Journey (PRD to Issues)
- **Agent Action:** Deconstruct the PRD into a Kanban board on GitHub Issues.
- **Decomposition Rules:**
  * Break tasks down into **"Vertical Slices" (Tracer Bullets)** that cut through all layers of the system (from Database to UI), rather than horizontal layers. This ensures immediate feedback.
  * Apply the **"Define errors out of existence"** principle early in the interface/API design phase. Design normal-case flows that naturally handle anomalies without throwing messy exceptions.

### 4️⃣ Step 4: Untouched Execution (AFK Loop & TDD)
- **Agent Action:** Automatically pick up unblocked GitHub Issues.
- **Coding Loop:**
  * **Write comments first (Ousterhout):** Write comments explaining "WHY" (design intent/rationale) and describe the interface before writing the actual implementation code.
  * **TDD Loop:** Write a failing test (Red) ➔ Write the minimal implementation code to pass (Green) ➔ Refactor.
  * **Momento Mode (Reset Context):** **You MUST clear the LLM context after completing and closing each Issue**. The next agent session must start with a clean context to prevent falling into the "Dumb zone".

### 5️⃣ Step 5: Simplify Architecture (Improve Codebase Architecture)
- **Agent Action:** Periodically scan the codebase to:
  * Detect and eliminate "Shallow Modules" caused by over-fragmentation ("Class-itis").
  * Merge them into "Deep Modules" with extremely clean interfaces.
  * Eliminate unnecessary dependencies and reduce codebase obscurity.

---

## 📂 DECISION LOGS & KNOWLEDGE SHARING

- **Task/Session Logs:** Updated and maintained in the flat [HANDOFF.md](file:///home/thienvu/workspace/BotAutoCRM/HANDOFF.md) file at the root of the workspace. Do not create local specifications or task checklists inside this repository.
- **Global Knowledge & Cross-Learning:** Traversed through the [global_brain](file:///home/thienvu/workspace/BotAutoCRM/global_brain/) directory (symlink pointing to `../AgentRoot/knowledge_base/`). Read pitfalls, standards, and global design principles before writing code.
