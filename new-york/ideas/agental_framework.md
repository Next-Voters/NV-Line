# Agental Framework

## High-level goal

Given a city name, the system finds official proposed legislation, understands what it is trying to do, and analyzes possible impacts using evidence from similar policies, then makes all of it searchable and explorable via RAG.

## Step-by-step system flow (simplified, engineered)

### 1) User inputs a city name

The user enters a city like Brampton or Chicago.

This triggers a discovery pipeline, not a fixed scraper.

### 2) Infer country and load the correct jurisdiction playbook

The system determines whether the city is in Canada or the United States.

It then loads a jurisdiction playbook as context for the AI.

#### Canada

- **Municipalities**
  - Agendas
  - Staff reports
  - Draft by-laws
- **Provinces/Territories**
  - Bills
  - Readings
  - Committees
- **Federal**
  - Bills
  - Committees
  - Legislative calendars

#### United States

- **Municipalities**
  - Ordinances
  - Resolutions
  - Council agendas
- **States**
  - Bills
  - Committee hearings
- **Federal**
  - Bills
  - Congressional sessions

The playbook does not change dynamically.

It exists to prevent the AI from guessing how legislation works.

### 3) Discover official legislative channels using Firecrawl

Using the city name + playbook context, the system searches for:

- Council or committee portals
- Agenda and minutes pages
- Legislative services or by-law pages

The system prioritizes official domains:

- `.ca`, `.gov`, city-owned domains
- Known municipal portal vendors (only if linked from official sites)

Random blogs and news articles are ignored.

### 4) Build a verified source registry for the city

Before scraping deeply, the system builds a source registry:

- Meeting index URL(s)
- Agenda pages
- Attachment hosting pages
- By-law or legislative listings

This registry is cached so the system doesn’t “re-learn” the city every time.

### 5) Crawl meetings and extract agenda items

From the source registry, the system:

- Pulls upcoming and recent meetings
- Extracts agenda items
- Collects all attachments (staff reports, draft by-laws, motions)

Everything is converted into structured data, not raw text.

### 6) Identify which items are proposed legislation

Not all agenda items matter.

The system filters for proposed legislation using:

- Document types (draft by-law, staff report, notice of motion)
- Keywords (amend, enact, approve, authorize)
- A lightweight classifier for edge cases

Each inclusion must be explainable.

### 7) Ingest documents and build the RAG index

For each proposed item:

- Documents are downloaded
- Text is extracted and chunked cleanly
- Metadata is attached (city, date, committee, item number, source)
- Content is vectorized into a vector database

This becomes the system’s grounded knowledge base.

### 8) Extract the objective of the proposed legislation

An agent reads the agenda item and attachments and produces a structured proposal brief:

- What is being proposed
- What changes if it passes
- Who is affected
- Timelines or implementation details

All claims are tied to source documents.

### 9) Run a graph-orchestrated impact analysis process

This is where LangGraph actually makes sense.

A branched workflow:

- Searches for similar legislation elsewhere
- Retrieves fact-based outcomes (reports, audits, studies)
- Loops and expands search if evidence is weak
- Tracks state across steps

This is a research subprocess, not a single prompt.

### 10) Synthesize impacts without pretending to predict the future

The system produces an impact brief that clearly separates:

- Observed outcomes (evidence-backed)
- Comparable outcomes (similar policies)
- Uncertainty and risks (explicitly labeled)

If evidence is thin, the system says so.

### 11) Enable user Q&A through RAG

Users can ask questions about the proposed legislation.

The system answers using retrieval-augmented generation:

- Filtered by city and proposal
- Grounded in indexed documents
- With citations to original sources

No free-wheeling answers.

### 12) Generate briefings and scale across cities

The system can generate weekly email briefings summarizing new proposals.

Each city runs as a separate queued job with:

- Rate limiting
- Incremental updates
- Retries and failure handling
- Caching and deduplication