"""
discoverer.py — Universal AI Research Planner
Analyzes user queries, generates clarifying questions, refines prompts,
and breaks down research tasks into structured vectors with targeted search queries.
"""
import json
import re
from engine import extractor


def _sanitize_ddg_query(query: str) -> str:
    """Strip search operators that DuckDuckGo can't handle (site:, OR, AND, parentheses, ..)."""
    # Remove site:domain.com patterns
    query = re.sub(r'site:\S+', '', query)
    # Remove other field operators such as filetype:pdf or intitle:report
    query = re.sub(r'\b\w+:\S+', '', query)
    # Remove boolean operators (as whole words)
    query = re.sub(r'\bOR\b', ' ', query, flags=re.IGNORECASE)
    query = re.sub(r'\bAND\b', ' ', query, flags=re.IGNORECASE)
    # Remove punctuation commonly used for search operators
    query = re.sub(r'[()"\'`]', ' ', query)
    # Remove range operators like 2023..2025
    query = re.sub(r'\d{4}\.\.\d{4}', '', query)
    # Collapse whitespace
    query = re.sub(r'\s+', ' ', query).strip()
    # Truncate very long queries (DDG struggles over ~150 chars)
    if len(query) > 150:
        query = query[:150].rsplit(' ', 1)[0]
    return query


def generate_clarifying_questions(query: str, context: str = '') -> dict:
    """
    Takes the user's raw research query and uses Gemini with a Fast/Strong pass split to:
    - Understand the topic and scope
    - Generate targeted clarifying questions and assumptions
    """
    if not extractor._clients:
        return {"success": False, "error": "Gemini not configured."}

    # 1. Fast Pass (cheap tier) to get topic, scope, and obvious questions
    fast_prompt = f"""You are a research planner. For the user query: "{query}" and context: "{context}", identify:
1. Short name of the main subject/industry being researched (detected_topic).
2. Brief description of the initial scope (detected_scope).
3. 1-2 most obvious clarifying questions.

Return as JSON matching this structure:
{{
  "detected_topic": "...",
  "detected_scope": "...",
  "obvious_questions": [
    {{
      "id": "q_id",
      "question": "...",
      "options": ["Option A", "Option B"],
      "type": "select", // select, multi-select, or text
      "default": "Option A"
    }}
  ]
}}
Return ONLY valid JSON. No markdown code blocks, no explanation."""

    detected_topic = ""
    detected_scope = ""
    obvious_questions = []

    try:
        response = extractor._call_gemini(
            contents=fast_prompt,
            tier="cheap",
            judgment=False,
            config=extractor.types.GenerateContentConfig(temperature=0.1)
        )
        parsed = extractor._parse_json_response(response.text)
        if parsed and isinstance(parsed, dict):
            detected_topic = parsed.get("detected_topic", "")
            detected_scope = parsed.get("detected_scope", "")
            obvious_questions = parsed.get("obvious_questions", [])
    except Exception as e:
        print(f"    [Fast Pass Clarification failed: {e}]")

    # 2. Strong Pass (strong tier) to get assumptions and judgment-heavy questions
    strong_prompt = f"""You are a master AI Research Planner. A user wants to research:
Query: "{query}"
Additional Context: "{context}"

We have performed a fast pass and detected:
Topic: "{detected_topic or 'Unknown'}"
Initial Scope: "{detected_scope or 'Unknown'}"
Obvious Questions: {json.dumps(obvious_questions)}

Identify key ambiguities and assumptions.
Generate 2-3 key assumptions that the user should confirm or correct.
Generate 1-2 additional judgment-heavy clarifying questions (e.g., target geography, business models, specific metrics needed).

Return as JSON matching this structure:
{{
  "assumptions": ["Assumption 1", "Assumption 2"],
  "additional_questions": [
    {{
      "id": "unique_question_id",
      "question": "...",
      "options": ["Option A", "Option B"],
      "type": "select",
      "default": "Option A"
    }}
  ]
}}
Return ONLY valid JSON. No markdown code blocks, no explanation."""

    assumptions = []
    additional_questions = []
    
    try:
        response = extractor._call_gemini(
            contents=strong_prompt,
            tier="strong",
            judgment=True,
            config=extractor.types.GenerateContentConfig(temperature=0.3)
        )
        parsed = extractor._parse_json_response(response.text)
        if parsed and isinstance(parsed, dict):
            assumptions = parsed.get("assumptions", [])
            additional_questions = parsed.get("additional_questions", [])
    except Exception as e:
        print(f"    [Strong Pass Clarification failed: {e}]")
        if not obvious_questions:
            # Fallback if both passes failed or strong pass failed and cheap had nothing
            return {"success": False, "error": f"Failed to plan research: {e}"}

    # Combine questions and add a default research depth question
    all_questions = obvious_questions + additional_questions
    
    # Check if a research depth question is already there
    has_depth_q = any("depth" in q.get("id", "").lower() or "depth" in q.get("question", "").lower() for q in all_questions)
    if not has_depth_q:
        all_questions.append({
            "id": "research_depth",
            "question": "What is the preferred depth of this research?",
            "options": ["Surface Level", "Medium Depth", "Deep Research"],
            "type": "select",
            "default": "Medium Depth"
        })

    # Return result
    return {
        "success": True,
        "questions": all_questions,
        "assumptions": assumptions,
        "detected_topic": detected_topic or query[:30],
        "detected_scope": detected_scope or query,
        "error": None
    }


def continue_clarifying_questions(query: str, previous_answers: list[dict], user_note: str, context: str = '') -> dict:
    """
    Continue the clarification loop after the user has answered initial questions
    and added free-form corrections, new ideas, or scope changes.
    """
    if not extractor._clients:
        return {"success": False, "error": "Gemini not configured."}

    answers_text = json.dumps(previous_answers, indent=2, default=str)

    prompt = f"""You are an expert AI Research Planner running an iterative clarification interview.

Original Query: "{query}"
Additional Context: "{context}"

The user has already answered these questions:
{answers_text}

The user then added this free-form clarification, correction, or new idea:
"{user_note}"

Your task:
1. Update your understanding of the research scope.
2. List the assumptions you now hold and that the user may still need to correct.
3. Ask only the remaining high-value follow-up questions needed to remove ambiguity.
4. If the scope is already clear, return an empty questions array.

Return your response in this exact JSON structure:
{{
  "detected_topic": "Short name of the main subject/industry being researched",
  "detected_scope": "Updated scope summary",
  "assumptions": ["Current assumption 1", "Current assumption 2"],
  "questions": [
    {{
      "id": "unique_question_id",
      "question": "The follow-up question text?",
      "options": ["Option A", "Option B", "Option C"],
      "type": "select",
      "default": "Option A"
    }}
  ]
}}

Return ONLY valid JSON. No explanations, no markdown code blocks."""

    try:
        response = extractor._call_gemini(
            contents=prompt,
            tier="strong",
            judgment=True,
            config=extractor.types.GenerateContentConfig(temperature=0.25)
        )
        raw_text = response.text
        parsed = extractor._parse_json_response(raw_text)

        if parsed and isinstance(parsed, dict) and "questions" in parsed:
            return {
                "success": True,
                "questions": parsed.get("questions", []),
                "assumptions": parsed.get("assumptions", []),
                "detected_topic": parsed.get("detected_topic", ""),
                "detected_scope": parsed.get("detected_scope", ""),
                "raw_response": raw_text,
                "error": None
            }

        return {
            "success": False,
            "questions": [],
            "assumptions": [],
            "detected_topic": "",
            "detected_scope": "",
            "raw_response": raw_text,
            "error": "Failed to parse structured JSON follow-up questions from Gemini."
        }
    except Exception as e:
        return {
            "success": False,
            "questions": [],
            "assumptions": [],
            "detected_topic": "",
            "detected_scope": "",
            "raw_response": "",
            "error": str(e)
        }


def refine_research_prompt(query: str, answers: list[dict], context: str = '') -> dict:
    """
    Takes the original query + user's answers to clarifying questions and generates:
    - A well-structured master research prompt (detailed, specific, unambiguous)
    - A list of 5-10 research vectors (independent sub-topics to explore)
    - Suggested data points to extract per vector
    - Quality criteria for source selection
    - Effort estimate scaled by depth
    """
    if not extractor._clients:
        return {"success": False, "error": "Gemini not configured."}
    
    # Format answers transcript verbatim
    formatted_answers = []
    for i, ans in enumerate(answers):
        q_text = ans.get("question_text") or ans.get("question") or ans.get("question_id") or "Question"
        a_text = ans.get("answer", "No answer provided")
        formatted_answers.append(f"Question {i+1}: {q_text}\nAnswer {i+1}: {a_text}\n")
    answers_transcript = "\n".join(formatted_answers)
    
    prompt = f"""You are a master Research Architect and text expander. Your job is to take a raw research query, combine it with the user's explicit answers to clarifying questions, and compile a definitive, highly detailed, and fully expanded research plan/brief.

CRITICAL REQUIREMENT: Do NOT rewrite, change, summarize, or drop any of the user's original query, answers, or core requests. The `refined_prompt` and the list of `vectors` MUST completely cover every detail, background context, specific company list, and requirement mentioned by the user. You are strictly forbidden from omitting, grouping away, or dropping any target company, product, regulatory body, or constraint (e.g., volume tiers, shipping services) from either the `refined_prompt` or the `vectors` list.

Specifically, inside the `refined_prompt` field of the returned JSON, you MUST structure it as follows:
1. "ORIGINAL USER QUERY": Reproduce the original query verbatim.
2. "CLARIFYING QUESTIONS & VERBATIM ANSWERS": List all the clarification questions and the user's answers verbatim.
3. "DETAILED RESEARCH REQUIREMENTS & INSTRUCTIONS": Expand on the query, describing the specific goals, constraints, target geography/market (e.g. India-specific escrow/payments regulations if applicable), and detailed parameters to research.
4. "REQUIRED DELIVERABLES CHECKLIST": Provide a clear, actionable list of all deliverables, comparisons, tables, Gantt charts, or flowcharts explicitly requested by the user.

Original Query: "{query}"
Additional Context: "{context}"
Clarification Answers Transcript:
{answers_transcript}

You must output a JSON object containing:
1. `refined_prompt`: The expanded master prompt as described above. Ensure all user inputs and cross-questioning responses are preserved verbatim and built upon.
2. `vectors`: A list of 5 to 10 independent research vectors (sub-topics/questions). Each vector should represent a distinct line of inquiry that can be researched in parallel. Crucially, ensure that every single target company, competitor, product, regulatory body, or specific research request mentioned in the original query or answers transcript is mapped to and addressed by at least one vector. Do not group them so broadly that specific companies or questions get merged or ignored; generate company-specific or detail-specific vectors as needed to ensure complete coverage.
3. `suggested_data_points`: Specific, measurable data points/metrics to extract across the research.
4. `quality_notes`: Specific instructions on what sources to trust based on the topic.
5. `target_authority_domains`: A JSON list of specific domain names, TLD patterns, or official website strings that are highly relevant to and authoritative for this specific research topic. Identify and list these target domains/platforms dynamically based on the exact query to avoid domain drift.
6. `required_deliverables`: A JSON checklist of all specific deliverables, questions, tables, comparisons, or items explicitly requested in the user's raw prompt or clarification replies.

JSON structure:
{{
  "refined_prompt": "...",
  "vectors": [
    {{
      "id": "vector_id",
      "topic": "Vector Title (e.g., [Company Name] Logistics Pricing, Surcharges Comparison, Industry Benchmarks)",
      "description": "Detailed explanation of what needs to be answered by this vector. Crucially, explicitly mention the specific target companies, products, or questions this vector is researching.",
      "search_hints": ["keyword 1", "keyword 2"],
      "data_points": ["parameter_1", "parameter_2"],
      "priority": "high"
    }}
  ],
  "suggested_data_points": ["data point A", "data point B"],
  "quality_notes": "...",
  "target_authority_domains": ["domain1.com", "domain2.gov"],
  "required_deliverables": ["Checklist Item 1", "Checklist Item 2"]
}}

Return ONLY valid JSON. No explanations, no markdown blocks."""

    try:
        response = extractor._call_gemini(
            contents=prompt,
            tier="strong",
            judgment=True,
            config=extractor.types.GenerateContentConfig(
                temperature=0.2,
            )
        )
        raw_text = response.text
        parsed = extractor._parse_json_response(raw_text)
        
        if parsed and isinstance(parsed, dict) and "vectors" in parsed:
            # Determine depth from answers to calculate effort estimate
            depth = "standard"
            for ans in answers:
                qid = ans.get("question_id", "").lower()
                val = str(ans.get("answer", "")).lower()
                if "depth" in qid:
                    if "surface" in val:
                        depth = "surface"
                    elif "deep" in val:
                        depth = "deep"
                    else:
                        depth = "standard"
                    break
            
            if depth == "surface":
                effort = { "sources_to_discover": 5, "pages_to_scrape": 10, "synthesis_passes": 1 }
            elif depth == "deep":
                effort = { "sources_to_discover": 30, "pages_to_scrape": 60, "synthesis_passes": 3 }
            else: # standard
                effort = { "sources_to_discover": 12, "pages_to_scrape": 25, "synthesis_passes": 2 }

            return {
                "success": True,
                "refined_prompt": parsed.get("refined_prompt", ""),
                "vectors": parsed.get("vectors", []),
                "suggested_data_points": parsed.get("suggested_data_points", []),
                "quality_notes": parsed.get("quality_notes", ""),
                "target_authority_domains": parsed.get("target_authority_domains", []),
                "required_deliverables": parsed.get("required_deliverables", []),
                "effort_estimate": effort,
                "depth": depth,
                "raw_response": raw_text,
                "error": None
            }
        else:
            return {
                "success": False,
                "refined_prompt": "",
                "vectors": [],
                "suggested_data_points": [],
                "quality_notes": "",
                "target_authority_domains": [],
                "required_deliverables": [],
                "raw_response": raw_text,
                "error": "Failed to parse structured JSON refined prompt from Gemini."
            }
    except Exception as e:
        return {
            "success": False,
            "refined_prompt": "",
            "vectors": [],
            "suggested_data_points": [],
            "quality_notes": "",
            "target_authority_domains": [],
            "required_deliverables": [],
            "raw_response": "",
            "error": str(e)
        }


def generate_blueprint(query: str, refined_prompt: str, vectors: list[dict], answers: list[dict]) -> dict:
    """
    Generate a dynamic document blueprint BEFORE scraping.
    The AI decides what headings the report needs based on the query and vectors,
    specifying content_type, mapped_vector_ids, source_affinity, and instructions.
    """
    if not extractor._clients:
        return {"sections": [], "presentation_rules": {}}

    prompt = f"""You are a master Document Architect. Your task is to design the ideal document blueprint/template structure for a comprehensive research report.
    
    Original Query: {query}
    Refined Research Prompt & Deliverables:
    {refined_prompt}
    
    Research Vectors:
    {json.dumps(vectors, indent=2)}
    
    Clarification Answers:
    {json.dumps(answers, indent=2)}
    
    You need to output a JSON object representing the document blueprint. The report should NOT use standard generic headings. It should have highly tailored, specific, and logical headings based on the query. For example, if the query is about "Competitor escrow for clothing startups in India", the sections could be:
    - Escrow Regulatory & Compliance Landscape in India
    - Key Transaction Milestones & Refund Trigger Workflows
    - Competitor Escrow Comparison Matrix
    - Platform-by-Platform Escrow Deep Dives (Craftsvilla, Jaypore, Glowroad, Meesho, etc.)
    - Best Practices & Integration Roadmap for Silaai
    
    For each section, specify:
    1. `id`: A unique string ID (e.g. `sec_compliance`, `sec_milestones`).
    2. `heading`: The tailored section title.
    3. `sub_headings`: An array of sub-heading strings.
    4. `content_type`: The primary visual format of the content. Must be one of:
       - `narrative` (paragraphs and lists)
       - `narrative_with_flowchart` (text and a Mermaid flowchart)
       - `flowchart` (primarily a Mermaid flowchart diagram)
       - `comparison_table` (a markdown comparison table comparing entities/platforms)
       - `data_matrix` (a structured parameters/data table)
       - `timeline` (a Mermaid timeline/gantt chart showing a roadmap/milestones)
    5. `mapped_vector_ids`: A list of IDs of the search vectors that contain relevant information for this heading. This connects search vectors to report sections (many-to-many).
    6. `source_affinity`: A list of specific domains or source patterns (e.g. ["rbi.org.in", "razorpay.com"]) that are particularly authoritative for this heading's topic.
    7. `instructions`: Specific guidance for the synthesizer on what to cover, what visual assets to produce, and what analysis to perform in this section. Make sure all requirements in the query and cross-questioning are fully covered.
    
    You must also output `presentation_rules`:
    - `use_flowcharts_for`: process flows, payment flows, customer journeys, transaction triggers.
    - `use_tables_for`: competitor parameter comparison, rate structures, feature tables.
    - `use_timelines_for`: roadmaps, transaction milestones, rollouts.
    - `embed_images`: true
    
    JSON structure:
    {{
      "document_title": "Ideal Report Title",
      "sections": [
        {{
          "id": "section_id",
          "heading": "Section Heading",
          "sub_headings": ["Sub-heading A", "Sub-heading B"],
          "content_type": "narrative_with_flowchart",
          "mapped_vector_ids": ["vector_id_1", "vector_id_2"],
          "source_affinity": ["domain1.com"],
          "instructions": "Detailed synthesizer instructions..."
        }}
      ],
      "presentation_rules": {{
        "use_flowcharts_for": [...],
        "use_tables_for": [...],
        "use_timelines_for": [...],
        "embed_images": true
      }}
    }}
    
    Return ONLY valid JSON. No markdown formatting blocks or explanations."""

    try:
        response = extractor._call_gemini(
            contents=prompt,
            config=extractor.types.GenerateContentConfig(temperature=0.2),
            tier="strong",
            judgment=True
        )
        parsed = extractor._parse_json_response(response.text)
        if parsed and isinstance(parsed, dict) and "sections" in parsed:
            return parsed
        return {"sections": [], "presentation_rules": {}}
    except Exception as e:
        print(f"Error generating blueprint: {e}")
        return {"sections": [], "presentation_rules": {}}


def generate_search_queries(vector: dict, context: str = '', depth: str = 'standard') -> list[str]:
    """
    For a given research vector, generate optimized search queries targeting different source types.
    Number of queries scales with depth:
    - surface: 3 queries
    - standard: 8 queries
    - deep: 15 queries
    """
    if not extractor._clients:
        return []

    topic = vector.get("topic", "")
    description = vector.get("description", "")
    hints = ", ".join(vector.get("search_hints", []))
    
    num_queries = 8
    if depth == "surface":
        num_queries = 3
    elif depth == "deep":
        num_queries = 15

    prompt = f"""You are a search query expert. Generate exactly {num_queries} simple search queries for DuckDuckGo to find information on the following research sub-topic.

Sub-Topic/Vector: "{topic}"
Description: "{description}"
Keywords/Hints: {hints}
Overall Context: "{context}"

CRITICAL RULES FOR QUERY FORMAT:
- Write plain, natural-language queries only
- Do NOT use any search operators: no site:, no OR, no AND, no parentheses, no quotes, no filetype:, no range operators like 2023..2025
- Keep each query SHORT (under 10 words ideally)
- Distribute queries to cover different source types: consulting reports, government databases, official company sites, libraries, and broad general query angles.

Return a JSON array of exactly {num_queries} query strings:
[
  "query 1",
  "query 2",
  ...
]

Return ONLY JSON. No explanations, no markdown blocks."""

    try:
        response = extractor._call_gemini(
            contents=prompt,
            config=extractor.types.GenerateContentConfig(temperature=0.2),
            tier="cheap",
            judgment=False
        )
        parsed = extractor._parse_json_response(response.text)
        if parsed and isinstance(parsed, list):
            return [_sanitize_ddg_query(q) for q in parsed if isinstance(q, str)]
        return [f"{topic} research", f"{topic} data", f"{topic} report"]
    except Exception:
        return [f"{topic} research", f"{topic} data", f"{topic} report"]


# Maintain backwards compatibility
def generate_research_plan(query: str, instruction: str = "") -> dict:
    """Legacy function. Maps to generate_clarifying_questions."""
    res = generate_clarifying_questions(query, instruction)
    if res["success"]:
        return {
            "success": True,
            "plan": {
                "proposed_entities": [res["detected_topic"]],
                "proposed_data_points": ["Market Size", "Key Players", "Pricing"],
                "clarifying_questions": res["questions"],
                "instruction_modifier": res["detected_scope"]
            },
            "raw_response": res["raw_response"]
        }
    return res
