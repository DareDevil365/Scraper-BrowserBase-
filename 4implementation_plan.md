# Implementation Plan: Blueprint-First Research & Premium Presentation Overhaul

This plan details the implementation of the expanded prompt refinement process (to prevent summarization/loss of user inputs), verbatim cross-questioning transcript retention, async global source queue fanning, blueprint-aware synthesis, and a premium presentation layer with interactive flowcharts and custom light/dark HSL themes.

---

## Proposed Changes

### Component 1: Prompt Expansion & Blueprint Generation

#### [MODIFY] [discoverer.py](file:///c:/Users/yasha/Desktop/scout/engine/discoverer.py)

1.  **Refactor `refine_research_prompt(query, answers, context)`**:
    *   Construct an explicit verbatim Q&A transcript string from the answers list.
    *   Instruct the Gemini model (strong tier) via a detailed prompt to act as a **text expander**, not a summarizer.
    *   Explicitly forbid rewriting or dropping any detail, target company, question, or constraint.
2.  **Refactor `generate_blueprint(query, refined_prompt, vectors, answers)`**:
    *   Ensure the generated report sections have customized titles that directly address the user's specific query.
    *   Assign each section a specific `content_type` (`narrative`, `flowchart`, `narrative_with_flowchart`, `comparison_table`, `data_matrix`, `timeline`).

---

### Component 2: Global Source Pool & Async Routing

#### [MODIFY] [deep_extractor.py](file:///c:/Users/yasha/Desktop/scout/engine/deep_extractor.py)

1.  **Enhance `route_urls_to_headings(urls, sections)`**:
    *   Utilize a batch AI categorization prompt to maps URL details to blueprint section IDs.
2.  **Enhance `discover_sources_for_session(...)`**:
    *   Integrate search query generation and domain authority boosting, writing results directly to `scrape_queue.json`.
3.  **Enhance `scrape_and_extract_for_pool(...)`**:
    *   Verify thread-safe worker execution and integrate `validate_page_entity` check.
4.  **Enhance `adaptive_rediscovery(...)`**:
    *   Generate section-specific search queries if headings remain undersourced after the queue is empty.

---

### Component 3: Blueprint-Aware Synthesis

#### [MODIFY] [extractor.py](file:///c:/Users/yasha/Desktop/scout/engine/extractor.py)

1.  **Enhance `synthesize_research_stream(...)`**:
    *   Synthesize report sections sequentially based on the blueprint sections.
    *   Inject the expanded master prompt and verbatim answers transcript directly into the synthesis prompts.
    *   Enforce visualization rules (Mermaid diagrams, markdown tables, Gantt charts) based on the section's `content_type`.
    *   Carry and feed summaries of previous sections to prevent redundant information.

---

### Component 4: Premium Presentation Overhaul

#### [MODIFY] [present.py](file:///c:/Users/yasha/Desktop/scout/present.py)

1.  **Inject Scope & Verbatim Clarifications into the Document Model**:
    *   In `build_document_model()`, retrieve the `original_query` and `clarification_answers` from the run configuration files (`run_config.json` or `state.json`) and pass them to the template model.
2.  **Enhance Markdown-to-HTML Parsing**:
    *   Update image tag processing to wrap markdown images (`![alt](url)`) in a `<div class="image-wrapper">` with an `<img class="report-img">` and a `<div class="image-fallback">` placeholder.
    *   Convert `language-mermaid` code blocks to `<div class="mermaid">` tags.
    *   Ensure Quality Gate Checks are run to screen output files for leakages like placeholders (`TODO`, `Insert Company`, `N/A`) or unrendered Jinja tags.

#### [MODIFY] [report_template.html](file:///c:/Users/yasha/Desktop/scout/templates/report_template.html)

1.  **Redesign with Curated HSL Dark/Light Colors**:
    *   Create a modern, clean palette using CSS variables (`--bg-main`, `--bg-card`, `--accent`, `--text-primary`, etc.) with glassmorphism backdrops and dynamic shadow effects.
2.  **Add a Verbatim Scope Compliance Panel**:
    *   Create a collapsible dashed-border panel (`<details class="compliance-panel">`) at the top of the report showing the original user query and verbatim transcripts of the cross-questioning interview questions and answers.
3.  **Dynamic Mermaid.js Rendering**:
    *   Load and initialize `mermaid.min.js` via CDN. Re-initialize diagrams programmatically whenever the dark/light theme is switched.
4.  **TOC Scroll-Spy and Theme Switching**:
    *   Add a scroll-spy JavaScript script to highlight the active section in the sticky sidebar table of contents as the user scrolls.
    *   Add a toggle button to switch themes.
5.  **Robust Image Fallbacks**:
    *   Add error-handling event listeners to all `.report-img` elements that automatically display a card with the source hostname and a link to view the image on the original website.

---

## Verification Plan

### Automated Verification
*   **Prompt Expansion Verification**:
    Run `python scratch/test_reforms.py` using `Ques.txt` inputs. Inspect the generated `01_search_parameters.md` to ensure:
    - The verbatim questions and answers are printed under the Q&A transcripts section.
    - The original query is fully intact.
    - The size of the `refined_prompt` string is detailed and does not summarize inputs.
*   **Leakage/Validation Test**:
    Run the leak tests in `present.py` to assert that no Jinja placeholders or forbidden strings (`[Insert Company]`, `TODO`, `N/A`) were output.
*   **Presentation Compiler**:
    Execute `python present.py outputs/<run_folder>`. Verify that `report.html` was generated. Open the HTML file and confirm Mermaid diagrams, tables, and fallback wrappers are rendered.

### Manual Verification
*   Open the report in a web browser. Inspect the collapsible panel "Scope & Clarifications Transcript" to verify that cross-questioning inputs are displayed accurately.
*   Validate responsiveness: Shrink the viewport to ensure the layout moves to single column and hides the left sidebar navigation menu.
