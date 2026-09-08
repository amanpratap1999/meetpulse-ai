import json
import re
import logging
from typing import List, Optional, Tuple
import httpx
from src.config import settings
from src.schemas import ActionItemExtract, TranscriptExtractionResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert executive assistant and project manager.
Your task is to analyze meeting transcripts and extract all concrete action items.
For each action item, extract:
- task: The specific deliverable or action to be completed.
- owner: The person responsible (if identifiable, else null).
- due_date: The deadline or timeframe mentioned (e.g. 'by Friday', 'next week', or null).
- confidence: A float between 0.0 and 1.0 indicating confidence.

You MUST respond ONLY with a JSON object matching this schema:
{
  "action_items": [
    {
      "task": "string",
      "owner": "string or null",
      "due_date": "string or null",
      "confidence": 1.0
    }
  ]
}
"""

def extract_mock_action_items(transcript: str) -> TranscriptExtractionResult:
    """
    Deterministic rule-based extractor used for offline testing, local CI, and development
    prior to entering a live LLM API key.
    """
    items: List[ActionItemExtract] = []
    # Parse transcript into speaker utterances and sentences
    segments: List[Tuple[Optional[str], str]] = []
    
    # Try finding speaker turns like "Alice: ... Bob: ..."
    speaker_turns = re.findall(r"(?:^|\s+)([A-Z][a-zA-Z0-9_]{1,15}):\s*([^:\n]+(?=(?:\s+[A-Z][a-zA-Z0-9_]{1,15}:|$)))", transcript)
    if speaker_turns:
        for spk, text in speaker_turns:
            for s in re.split(r"[.!?]\s+", text):
                if s.strip():
                    segments.append((spk.strip(), s.strip()))
    else:
        for line in transcript.splitlines():
            line_clean = line.strip()
            if not line_clean:
                continue
            speaker_match = re.match(r"^([A-Z][a-zA-Z0-9_\s]{1,15}):\s*(.*)$", line_clean)
            spk = speaker_match.group(1).strip() if speaker_match else None
            cnt = speaker_match.group(2).strip() if speaker_match else line_clean
            for s in re.split(r"[.!?]\s+", cnt):
                if s.strip():
                    segments.append((spk, s.strip()))
                    
    due_date_patterns = [
        r"(by\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|eod|end of day|next week|end of week|this afternoon|3pm|noon|next sprint|this evening|morning|[\w\s\d]+?))(?:\.|$|\s)",
        r"(before\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|end of week|next sprint|thursday|[\w\s\d]+?))(?:\.|$|\s)",
        r"(due\s+[\w\s]+?)(?:\.|$|\s)"
    ]

    action_cues = ["will", "needs to", "need to", "action item", "todo", "handle", "prepare", "send", "review", "schedule", "deploy", "update", "fix", "write", "migrate", "verify", "investigate", "rotate", "design", "set up", "audit", "refactor", "provision", "order", "configure", "publish", "optimize", "increase", "export", "capture", "compile", "draft", "benchmark", "build", "interview", "analyze", "parallelize", "prune"]

    for speaker, content in segments:
        lower_content = content.lower()
        has_action = any(cue in lower_content for cue in action_cues)
        if not has_action:
            continue
            
        # Extract due date
        due_date = None
        for pattern in due_date_patterns:
            m = re.search(pattern, lower_content)
            if m:
                due_date = m.group(1).strip()
                break

        # Determine owner
        owner = None
        if speaker and any(w in lower_content for w in ["i will", "i'll", "i can", "i shall"]):
            owner = speaker
        else:
            name_match = re.search(r"\b([A-Z][a-z]+)\s+(?:will|to|should|is going to)\b", content)
            if name_match:
                owner = name_match.group(1)
            elif speaker:
                owner = speaker

        # Extract task description
        task_match = re.search(r"(?:i will|i'll|i can|will|to)\s+(.*)", content, re.IGNORECASE)
        task = task_match.group(1).strip() if task_match else content.strip()
        task = re.sub(r"^[-*•\d.]+\s*", "", task)

        items.append(
            ActionItemExtract(
                task=task,
                owner=owner,
                due_date=due_date,
                confidence=0.95
            )
        )
            
    # If no items found via heuristics, provide at least one summary action item if transcript is non-empty
    if not items and len(transcript.strip()) > 20:
        items.append(
            ActionItemExtract(
                task=f"Review meeting notes: {transcript.strip()[:60]}...",
                owner=None,
                due_date=None,
                confidence=0.70
            )
        )
        
    return TranscriptExtractionResult(action_items=items)


async def extract_action_items(transcript: str) -> TranscriptExtractionResult:
    """
    Extracts structured action items from a transcript using configured LLM provider or Mock.
    """
    if settings.MOCK_LLM or not settings.LLM_API_KEY:
        logger.info("Using mock LLM extractor (MOCK_LLM=True or LLM_API_KEY empty)")
        return extract_mock_action_items(transcript)

    # Live LLM Extraction
    base_url = "https://api.groq.com/openai/v1/chat/completions" if settings.LLM_PROVIDER == "groq" else "https://api.openai.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract all action items from this meeting transcript:\n\n{transcript}"}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(base_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return TranscriptExtractionResult(**parsed)
        except Exception as e:
            logger.error(f"LLM extraction error: {e}. Falling back to mock extractor.")
            # Graceful degradation with fallback
            return extract_mock_action_items(transcript)
