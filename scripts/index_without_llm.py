"""One-off: index a document into the RAG store without the LLM analyze step
(entity extraction / summarization / validation), for use when API credits
are unavailable. Mirrors ingestion_graph.py's load -> sectionize -> index ->
persist path, skipping 'analyze'. Backfill entities/summaries later via
`contract-intel ingest --force` once credits are available.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

from contract_intel.config import get_settings
from contract_intel.ingestion.chunking import sections_to_chunks
from contract_intel.ingestion.loaders import load_document
from contract_intel.ingestion.sectionizer import split_into_sections
from contract_intel.llm.provider import get_embeddings
from contract_intel.models.document import DocumentMetadata, ParsedDocument
from contract_intel.store import vector_store
from contract_intel.store.hashing import content_hash
from contract_intel.store.local_store import LocalStore


def main(file_path: str) -> None:
    settings = get_settings()
    store = LocalStore(settings.data_dir)
    path = Path(file_path)

    doc_id = content_hash(path.read_bytes())
    if store.find_by_content_hash(doc_id):
        print(f"Already ingested as doc_id={doc_id}")
        return

    raw_text, file_type = load_document(path)
    sections = split_into_sections(raw_text)
    print(f"Split into {len(sections)} sections")
    for s in sections:
        print(f"  [{s.section_id}] number={s.number!r} heading={s.heading!r}")

    chunks = sections_to_chunks(doc_id, sections, settings.chunk_size, settings.chunk_overlap)
    print(f"Built {len(chunks)} chunks for embedding")

    embeddings = get_embeddings(settings)
    index = vector_store.build_index(chunks, embeddings)
    index_path = vector_store.index_path(settings.data_dir, doc_id)
    vector_store.save_index(index, index_path)

    metadata = DocumentMetadata(
        doc_id=doc_id,
        filename=path.name,
        source_path=str(path),
        content_hash=doc_id,
        file_type=file_type,
        num_sections=len(sections),
        ingested_at=datetime.now(timezone.utc),
        needs_human_review=True,  # entities/summaries/validation not yet run
    )
    parsed = ParsedDocument(metadata=metadata, sections=sections)
    store.save_parsed_document(parsed)

    print(f"Indexed and persisted. doc_id={doc_id}")


if __name__ == "__main__":
    main(sys.argv[1])
