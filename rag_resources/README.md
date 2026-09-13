# CivicAgent PK — Data

This folder contains the verified project datasets used by the RAG/classification prototype.

## Files

### `civic_policies.json`

12 RAG-ready policy/legal records supplied through the team dataset and normalized for ChromaDB ingestion.

Each record includes:

- `id`
- `title`
- `category`
- `authority`
- `source_type`
- `source`
- `scope_region`
- `text`
- `official_url`
- `rag_metadata`
- `testing_note`

The records are based on official government/legal sources and include jurisdiction notes so the RAG system does not blindly apply a provincial or ICT rule to another region.

**Important:** These are RAG knowledge records, not legal advice. The system should retrieve the relevant official source and avoid making unsupported legal conclusions.

### `complaint_test_cases.json`

30 complaint test cases covering:

- English
- Roman Urdu
- Mixed-language complaints
- Solid waste
- Water supply
- Sewerage/drainage
- Roads/streets
- Street lighting
- Public cleanliness
- Other municipal services
- Easy, medium, and hard classification cases

These are primarily for classification/RAG testing and are not automatically ingested into ChromaDB as policy documents.

## Data coverage

The current dataset is sufficient for the hackathon prototype and for testing the current RAG pipeline. It is **not sufficient for production civic/legal guidance**.

Before production use, the knowledge base should be expanded with:

1. Current province/local-government rules for the exact target deployment area.
2. More specific service-level rules for water, sewerage, roads, street lighting, waste collection and sanitation.
3. Current responsible departments/authorities and their complaint channels.
4. More official source documents rather than broad landing pages where possible.
5. More complaint-policy mappings so each test case can be evaluated against an expected policy.
6. Additional jurisdictions/services if the final product will support more than the currently covered regions.

## Refreshing ChromaDB

After changing `civic_policies.json`, run:

```powershell
python ingest_policies.py
```

The ingestion script uses the policy records' `id` and `text` fields and stores the remaining supported fields as ChromaDB metadata.

Do not commit `.env`, API keys, or local ChromaDB data.
