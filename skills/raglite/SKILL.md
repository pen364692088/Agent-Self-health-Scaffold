---
name: raglite
version: 1.0.8
description: "Local-first RAG cache: distill docs into structured Markdown, then index/query with Chroma (vector) + ripgrep (keyword)."
tags: [latest=1.0.8, local-first=1.0.8, prompt-injection=1.0.8, rag=1.0.8, security=1.0.8]
metadata:
  clawdbot:
    emoji: "🔍"
---

# RAGLite - Local-First RAG Cache

**Local-first RAG cache: distill docs into structured Markdown, then index/query with Chroma (vector) + ripgrep (keyword).**

RAGLite provides a secure, local-first retrieval-augmented generation system that processes documents into structured knowledge and enables fast, accurate querying without external dependencies.

## Core Philosophy

Traditional RAG systems rely on external APIs and cloud services.
RAGLite keeps everything local, secure, and under your control.

## Key Features

### 🏠 Local-First Architecture
- All processing happens locally
- No external API dependencies
- Full data privacy and control
- Offline operation capability

### 📚 Document Processing
- Markdown distillation of complex documents
- Structured knowledge extraction
- Automatic chunking and organization
- Metadata preservation

### 🔍 Dual Search System
- **Vector Search**: ChromaDB for semantic similarity
- **Keyword Search**: ripgrep for exact text matching
- Combined results for comprehensive coverage
- Configurable search strategies

### 🛡️ Security Focus
- Prompt injection protection
- Local data processing only
- No data transmission to external services
- User-controlled access permissions

## Usage

```bash
# Add documents to the knowledge base
raglite add ./docs/ --format "markdown" --recursive

# Search the knowledge base
raglite search "machine learning algorithms" --method "hybrid"

# Query with specific context
raglite query "How does RAGLite handle security?" --context "prompt-injection"

# Index management
raglite index --rebuild
raglite index --stats

# Export processed knowledge
raglite export --format "json" --output "./knowledge-export.json"
```

## Document Processing Pipeline

### 1. Ingestion
```bash
raglite ingest --source "./documents/" --formats ["pdf", "md", "txt", "docx"]
```

### 2. Distillation
- Extract key information
- Structure into Markdown
- Preserve metadata and relationships
- Generate summaries and abstracts

### 3. Chunking
- Intelligent document segmentation
- Context-aware chunk boundaries
- Overlap preservation for continuity
- Size optimization for processing

### 4. Indexing
- Vector embeddings with sentence-transformers
- Keyword indexing with ripgrep
- Metadata and cross-references
- Efficient storage structures

## Search Capabilities

### Vector Search
```bash
raglite search "semantic query" --method "vector" --top-k 10
```

### Keyword Search
```bash
raglite search "exact phrase" --method "keyword" --case-sensitive
```

### Hybrid Search
```bash
raglite search "query" --method "hybrid" --weights "vector:0.7,keyword:0.3"
```

### Contextual Search
```bash
raglite search "query" --context "technical documentation" --filter "date:2024"
```

## Configuration

```yaml
raglite:
  # Storage
  data_directory: "./raglite-data"
  max_storage_size: "10GB"
  
  # Processing
  chunk_size: 512
  chunk_overlap: 50
  embedding_model: "all-MiniLM-L6-v2"
  
  # Search
  default_top_k: 5
  vector_weight: 0.7
  keyword_weight: 0.3
  
  # Security
  prompt_injection_protection: true
  access_logging: true
  local_only: true
```

## Security Features

### Prompt Injection Protection
- Input sanitization and validation
- Query pattern analysis
- Malicious prompt detection
- Safe query construction

### Data Privacy
- Local-only processing
- No external data transmission
- User-controlled data retention
- Secure storage encryption

### Access Control
- Role-based permissions
- Query logging and auditing
- Rate limiting and throttling
- Content filtering options

## Integration

### API Integration
```python
import raglite

# Initialize
rag = raglite.RAGLite("./data")

# Add documents
rag.add_document("./doc.pdf")

# Search
results = rag.search("machine learning", method="hybrid")
```

### Tool Integration
- OpenClaw skills and agents
- Document processing pipelines
- Knowledge management systems
- Chat and assistant interfaces

## Performance Optimization

### Indexing Performance
- Parallel document processing
- Incremental indexing updates
- Efficient storage compression
- Smart caching strategies

### Query Performance
- Result caching and memoization
- Parallel search execution
- Optimized ranking algorithms
- Fast result retrieval

## Monitoring and Analytics

```bash
# Usage statistics
raglite stats --detailed

# Search analytics
raglite analytics --queries --timeframe "7d"

# System health
raglite health --verbose
```

## Best Practices

1. **Regular Updates**: Keep documents current and reindex periodically
2. **Quality Control**: Review and curate processed documents
3. **Security First**: Enable all security features for sensitive data
4. **Performance Tuning**: Adjust chunk sizes and search weights based on use case
5. **Backup Strategy**: Regular backups of knowledge base and indexes

## Troubleshooting

### Common Issues
- **Slow Search**: Check index size and consider rebuilding
- **Poor Results**: Adjust search weights and chunking parameters
- **Memory Issues**: Limit concurrent queries and optimize storage
- **Processing Errors**: Validate document formats and permissions

## Advanced Features

### Custom Embeddings
```bash
raglite configure --embedding-model "custom-model" --model-path "./models/"
```

### Query Expansion
```bash
raglite search "query" --expand --synonyms --related-concepts
```

### Multi-Modal Support
```bash
raglite add --images "./diagrams/" --extract-text
```

RAGLite provides a secure, efficient, and privacy-focused RAG solution that keeps your knowledge local and your data under your control.