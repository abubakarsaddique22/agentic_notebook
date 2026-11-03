"""Run a real NeMo LLMRails profile. No Promptfoo, LangChain or custom classifier."""
import argparse
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv
from nemoguardrails import LLMRails, RailsConfig

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
PROFILES = {
    'input': '01_input_prompt_injection',
    'output': '02_output_safety',
    'dialog': '03_dialog_colang',
    'retrieval': '04_rag_retrieval',
    'pii': '05_pii',
    'jailbreak': '06_jailbreak',
    'tools': '07_actions_execution',
    'combined': '08_combined',
}

@lru_cache(maxsize=8)
def load_rails(profile: str) -> LLMRails:
    config_dir = ROOT / 'lessons' / PROFILES[profile] / 'config'
    config = RailsConfig.from_path(str(config_dir))
    return LLMRails(config)

def handle(message: str, profile: str = 'input') -> str:
    """NeMo handles both generation and its configured rails in one call."""
    if profile not in PROFILES:
        raise ValueError(f'Unknown profile: {profile}')
    result = load_rails(profile).generate(messages=[{'role': 'user', 'content': message}])
    return str(result.get('content', '')) if isinstance(result, dict) else str(result)

def main():
    parser = argparse.ArgumentParser(description='NeMo Guardrails learning CLI')
    parser.add_argument('--lesson', choices=PROFILES, default='input')
    parser.add_argument('--once', help='Send a single question and exit')
    args = parser.parse_args()
    if args.once:
        print(handle(args.once, args.lesson))
        return
    print(f'NeMo-only lesson: {args.lesson}. Type exit to quit.')
    while True:
        try:
            message = input('You: ').strip()
        except (KeyboardInterrupt, EOFError):
            break
        if message.lower() in {'exit', 'quit'}:
            break
        if message:
            try:
                print('Assistant:', handle(message, args.lesson))
            except Exception as exc:
                print(f'NeMo/model error: {type(exc).__name__}: {exc}')
                print('Verify Ollama endpoint/model, NeMo version, and lesson config.')
if __name__ == '__main__':
    main()
