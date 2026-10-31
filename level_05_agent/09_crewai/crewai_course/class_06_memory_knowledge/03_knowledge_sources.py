"""
=====================================================================
 CLASS 06 | FILE 03: knowledge_sources.py
=====================================================================
 CONCEPT: Knowledge (RAG built-in)
 Kya hai : Knowledge = agent ki "reference library". Aap documents
           (text, PDF, CSV, Excel, JSON) dete ho, CrewAI unhein chhote
           tukron (chunks) mein kaat ke vector database mein rakhta hai.
           Task chalte waqt relevant tukre khud dhoond ke agent ko de
           deta hai. Isay hi RAG kehte hain.

 MEMORY vs KNOWLEDGE:
   Memory    -> jo kaam karte karte SEEKHA (badalta rehta hai)
   Knowledge -> jo aap ne PEHLE SE diya (policy, catalog, docs)

 Levels:
   Agent(knowledge_sources=[...]) -> sirf ye agent use karega
   Crew(knowledge_sources=[...])  -> crew ke sab agents use karenge

 Path note: file ka naam STRING mein doge to CrewAI root ke
   "knowledge/" folder mein dhoondta hai. Hum Path object de rahe hain
   taake is class ka apna knowledge folder use ho.

 Run:
     uv run python class_06_memory_knowledge/03_knowledge_sources.py
=====================================================================
"""

from pathlib import Path

from crewai import Agent, Task, Crew
from crewai.knowledge.knowledge_config import KnowledgeConfig
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.knowledge.source.csv_knowledge_source import CSVKnowledgeSource

from llm_setup import get_llm, EMBEDDER

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"

# ---------- 3 qisam ke sources ----------
about_store = StringKnowledgeSource(
    content="TimeHouse is an online watch store that started in Lahore in 2024."
)
policy_file = TextFileKnowledgeSource(file_paths=[KNOWLEDGE_DIR / "store_policy.txt"])
products_csv = CSVKnowledgeSource(file_paths=[KNOWLEDGE_DIR / "products.csv"])

support = Agent(
    role="Store Support Agent",
    goal="Answer only from the store's official information",
    backstory="You never make up policies. If the info is not available, you say so clearly.",
    llm=get_llm(temperature=0.0),
    knowledge_sources=[about_store, policy_file, products_csv],   # <-- knowledge
    embedder=EMBEDDER,
    knowledge_config=KnowledgeConfig(results_limit=4, score_threshold=0.3),
)

task = Task(
    description="Customer question: '{question}'",
    expected_output="A direct answer based on the store info (2-4 lines).",
    agent=support,
)

crew = Crew(agents=[support], tasks=[task])

questions = [
    "Can I return a watch after 10 days?",
    "Is the Black Leather Chrono in stock? What is the price?",
    "How many days will delivery to Multan take?",
]

for q in questions:
    result = crew.kickoff(inputs={"question": q})
    print(f"\nQ: {q}\nA: {result.raw}")

# ------------------------------------------------------------------
# PDF ke liye:  from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
#               PDFKnowledgeSource(file_paths=[KNOWLEDGE_DIR / "catalog.pdf"])
# KnowledgeConfig: results_limit = kitne chunks, score_threshold = kitna match zaroori
# ------------------------------------------------------------------
