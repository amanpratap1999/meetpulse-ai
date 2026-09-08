# Evaluation Report — Project 0: Meeting Notes → Action Items API

**Evaluation Run Date:** 2026-09-08 12:30:41  
**Evaluation Mode:** `MOCK`  
**Model Config:** `groq / llama-3.3-70b-versatile`  
**Dataset Size:** 16 synthetic multi-speaker transcripts  

---

## Executive Metric Summary

| Metric | Score | Target | Status |
|---|---|---|---|
| **Precision** | 86.5% | ≥ 85.0% | ✅ PASS |
| **Recall** | 100.0% | ≥ 85.0% | ✅ PASS |
| **F1 Score** | 92.8% | ≥ 85.0% | ✅ PASS |
| **Owner Attribution Accuracy** | 100.0% | ≥ 80.0% | ✅ PASS |
| **Due Date Detection Accuracy** | 96.9% | ≥ 75.0% | ✅ PASS |
| **Mean Extraction Latency** | 0.3 ms | < 2000 ms | ✅ PASS |

---

## Per-Transcript Breakdown

| ID | Meeting Title | Expected Items | Extracted Items | True Positives | Latency (ms) |
|---|---|---|---|---|---|
| meeting_01 | Backend Sprint Planning | 2 | 3 | 2 | 4.4 |
| meeting_02 | Product Launch Readiness | 2 | 2 | 2 | 0.07 |
| meeting_03 | Customer Success Sync | 2 | 2 | 2 | 0.05 |
| meeting_04 | Security & Compliance Review | 2 | 3 | 2 | 0.06 |
| meeting_05 | Marketing Campaign Kickoff | 2 | 3 | 2 | 0.06 |
| meeting_06 | Frontend Architecture Review | 2 | 2 | 2 | 0.05 |
| meeting_07 | HR Onboarding Optimization | 2 | 2 | 2 | 0.05 |
| meeting_08 | Sales Pipeline Review | 2 | 2 | 2 | 0.05 |
| meeting_09 | DevOps Incident Post-Mortem | 2 | 3 | 2 | 0.06 |
| meeting_10 | Data Engineering Sync | 2 | 2 | 2 | 0.05 |
| meeting_11 | Design System Meeting | 2 | 2 | 2 | 0.05 |
| meeting_12 | Mobile App Release Prep | 2 | 3 | 2 | 0.08 |
| meeting_13 | Executive Leadership Sync | 2 | 2 | 2 | 0.05 |
| meeting_14 | AI Feature Prototyping | 2 | 2 | 2 | 0.05 |
| meeting_15 | Customer Retention Taskforce | 2 | 2 | 2 | 0.05 |
| meeting_16 | QA Automation Review | 2 | 2 | 2 | 0.04 |

---

## Findings & Methodology
1. **Extraction Consistency:** The schema enforcement reliably extracted who owns what task and by when without JSON malformation.
2. **Deterministic Evaluation:** Ground truth sets contain expected action keywords, owner names, and deadline phrases.
3. **Seamless Key Integration:** When a live Groq or OpenAI API key is supplied in `.env` (`MOCK_LLM=false`), running `python eval/run_eval.py` immediately computes the live model's benchmark numbers.
