# Integration limitations

1. A LangChain tool's Chroma output is not automatically inside NeMo's retrieval pipeline. `search_knowledge` runs a shared heuristic screening helper; native `rails.retrieval` is for NeMo-mediated retrieval. Malicious documents can evade keyword checks; this is NOT a complete prompt-injection defense.
2. Authorization and approval are application tool-boundary functions; they are not native NeMo execution rails. CLI role flags are not verified authentication.
3. Built-in input/output self-checks are probabilistic and may fail. Presidio requires optional language resources.
4. Optional distilgpt2 score is for observation; not a validated jailbreak detector. No arbitrary threshold is enabled.
5. No test of the actual Ollama agent, tokenizer download or real guardrail enforcement has been performed in this environment. Treat all live behaviors as unverified until exercised locally.
6. No unrestricted agent actions or external IT operations are executed. Tickets are only pending records. The original human-review CLI was part of the removed security phase and is not included; records can still be reviewed by app developers using business code, not by prompt instructions.
