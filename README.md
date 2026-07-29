# policy-eval

## policies/
Structured, section-numbered text versions of insurance policy documents, prepared for RAG ingestion. Each coverage line item is its own numbered section so retrieval hits a single clause instead of a whole page.

## scripts/
`index_without_llm.py` — indexes a policy document into a [ContractIntel](https://github.com/) FAISS RAG store without running ContractIntel's LLM analyze step (entity extraction / summarization / validation). Useful when LLM API credits aren't available; embeddings are local (HuggingFace), so no API key is required for this step.

**Dependency**: this script imports from the `contract_intel` package and must be run from within a ContractIntel checkout with its virtualenv active:

```bash
cd /path/to/ContractIntel
source .venv/bin/activate
python /path/to/policy-eval/scripts/index_without_llm.py <path-to-policy.txt>
```

To backfill entities/summaries once LLM credits are available, run ContractIntel's normal CLI instead:

```bash
contract-intel ingest <path-to-policy.txt> --force
```
