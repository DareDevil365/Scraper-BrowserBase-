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
    Takes the user's raw research query and uses Gemini with a single Mid-tier pass to:
    - Understand the topic and scope
    - Generate targeted clarifying questions and assumptions
    """
    if not extractor._clients:
        return {"success": False, "error": "Gemini not configured."}

    prompt = f"""You are a research planner. For the user query: "{query}" and context: "{context}", identify:
1. Short name of the main subject/industry being researched (detected_topic).
2. Brief description of the initial scope (detected_scope).
3. 2-3 key assumptions that the user should confirm or correct.
4. 3-4 clarifying questions (a mix of obvious questions and judgment-heavy questions like target geography, business models, specific metrics needed).

Return as JSON matching this structure:
{{
  "detected_topic": "...",
  "detected_scope": "...",
  "assumptions": ["Assumption 1", "Assumption 2"],
  "questions": [
    {{
      "id": "unique_question_id",
      "question": "The question text?",
      "options": ["Option A", "Option B"],
      "type": "select", // select, multi-select, or text
      "default": "Option A"
    }}
  ]
}}"""

    try:
        response = extractor._call_gemini(
            contents=prompt,
            config=extractor.types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json"
            ),
            tier="mid",
            judgment=False
        )
        parsed = extractor._parse_json_response(response.text)
        if parsed and isinstance(parsed, dict):
            detected_topic = parsed.get("detected_topic", "")
            detected_scope = parsed.get("detected_scope", "")
            assumptions = parsed.get("assumptions", [])
            all_questions = parsed.get("questions", [])
            
            # Combine questions and add a default research depth question
            has_depth_q = any("depth" in q.get("id", "").lower() or "depth" in q.get("question", "").lower() for q in all_questions)
            if not has_depth_q:
                all_questions.append({
                    "id": "research_depth",
                    "question": "What is the preferred depth of this research?",
                    "options": ["Surface Level", "Medium Depth", "Deep Research"],
                    "type": "select",
                    "default": "Medium Depth"
                })

            return {
                "success": True,
                "questions": all_questions,
                "assumptions": assumptions,
                "detected_topic": detected_topic or query[:30],
                "detected_scope": detected_scope or query,
                "error": None
            }
    except Exception as e:
        print(f"    [Clarification failed: {e}]")
        
    return {
        "success": True,
        "questions": [
            {
                "id": "research_depth",
                "question": "What is the preferred depth of this research?",
                "options": ["Surface Level", "Medium Depth", "Deep Research"],
                "type": "select",
                "default": "Medium Depth"
            }
        ],
        "assumptions": [],
        "detected_topic": query[:30],
        "detected_scope": query,
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
}}"""

    try:
        response = extractor._call_gemini(
            contents=prompt,
            tier="strong",
            judgment=True,
            config=extractor.types.GenerateContentConfig(
                temperature=0.25,
                response_mime_type="application/json"
            )
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
    - A list of up to 30 research vectors (independent sub-topics to explore)
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
    
    prompt = f"""You are a master Research Architect. Take the raw query, combine it with the clarification answers, and compile a detailed research plan.

CRITICAL: Do NOT omit, summarize, or drop any user requests, target companies, or products. The vectors and refined_prompt MUST cover everything.

Original Query: "{query}"
Context: "{context}"
Answers Transcript:
{answers_transcript}

Output JSON structure:
{{
  "refined_prompt": "Expanded master prompt reproducing original query, answers, requirements, and deliverables verbatim.",
  "vectors": [
    {{
      "id": "vector_id",
      "topic": "Vector Title (granular, specific)",
      "description": "Specific questions/topics this vector researches (mention target companies/products explicitly).",
      "search_hints": ["keyword1", "keyword2"],
      "data_points": ["param1", "param2"],
      "priority": "high|medium|low"
    }}
  ],
  "suggested_data_points": ["metric A", "metric B"],
  "quality_notes": "Source credibility guidelines.",
  "target_authority_domains": ["domain1.com", "domain2.gov"],
  "required_deliverables": ["Deliverable checklist item"]
}}"""

    try:
        response = extractor._call_gemini(
            contents=prompt,
            tier="strong",
            judgment=True,
            config=extractor.types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json"
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

    prompt = f"""You are a Document Architect. Design a tailored document structure for a research report. Avoid generic headings.

Original Query: {query}
Refined Prompt: {refined_prompt}
Vectors: {json.dumps(vectors)}
Answers: {json.dumps(answers)}

Output JSON:
{{
  "document_title": "Ideal Report Title",
  "sections": [
    {{
      "id": "section_id",
      "heading": "Tailored Section Title",
      "sub_headings": ["Sub-heading A"],
      "content_type": "narrative|narrative_with_flowchart|flowchart|comparison_table|data_matrix|timeline",
      "mapped_vector_ids": ["vector_id_1"],
      "source_affinity": ["domain.com"],
      "instructions": "Specific guidance for the synthesizer on what to cover."
    }}
  ],
  "presentation_rules": {{
    "use_flowcharts_for": ["process flows"],
    "use_tables_for": ["comparisons"],
    "use_timelines_for": ["roadmaps"],
    "embed_images": true
  }}
}}"""

    try:
        response = extractor._call_gemini(
            contents=prompt,
            config=extractor.types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json"
            ),
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
    topic = vector.get("topic", "")
    hints = vector.get("search_hints", [])
    
    num_queries = 8
    if depth == "surface":
        num_queries = 3
    elif depth == "deep":
        num_queries = 15

    entity = topic
    words = topic.split()
    if len(words) > 1:
        entity = words[0]
        
    templates = [
        "{topic} {hint}",
        "{topic} official site",
        "{topic} pricing details",
        "{topic} guide and documentation",
        "{entity} competitor analysis",
        "{topic} review opinion",
        "{topic} features and comparison",
        "{entity} {hint} india",
        "official {topic} documentation",
        "how to integrate {entity} {hint}",
        "{topic} rules and regulations",
        "{topic} limits and fees",
        "{topic} process flow",
        "{entity} API specs",
        "{topic} latest updates 2025"
    ]
    
    queries = []
    for i, temp in enumerate(templates):
        hint = hints[i % len(hints)] if hints else "details"
        q = temp.format(topic=topic, entity=entity, hint=hint)
        clean_q = _sanitize_ddg_query(q)
        if clean_q and clean_q not in queries:
            queries.append(clean_q)
            
    while len(queries) < num_queries:
        queries.append(_sanitize_ddg_query(f"{topic} details {len(queries)}"))
        
    return queries[:num_queries]



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
