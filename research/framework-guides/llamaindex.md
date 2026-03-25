# LlamaIndex Hardening Guide

> Defence recommendations for LlamaIndex-based RAG and agentic applications,
> mapped to the AVE vulnerability database.

## Overview

LlamaIndex specialises in data-augmented LLM applications — RAG pipelines,
structured data extraction, and agentic query engines. Its deep integration
with external data sources introduces specific attack surfaces around
memory, schema, and data provenance.

---

## 1. Epistemic Contagion (AVE-2025-0009)

**Risk**: Corrupted knowledge in vector indices propagates to all queries
that retrieve from the poisoned embeddings, creating systemic hallucinations.

### LlamaIndex-Specific Vector

```python
# VULNERABLE — single index, no provenance tracking
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

documents = SimpleDirectoryReader("./data").load_data()
index = VectorStoreIndex.from_documents(documents)
# No source verification, no integrity checks
```

### Hardened Pattern

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Document
from llama_index.core.schema import TextNode
import hashlib
from datetime import datetime

class ProvenanceTracker:
    """Track document provenance for integrity verification."""

    def __init__(self):
        self.provenance_db = {}

    def ingest_with_provenance(self, doc: Document) -> Document:
        """Add provenance metadata before indexing."""
        content_hash = hashlib.sha256(doc.text.encode()).hexdigest()

        doc.metadata.update({
            "content_hash": content_hash,
            "ingestion_time": datetime.utcnow().isoformat(),
            "source_verified": self._verify_source(doc),
            "trust_score": self._compute_trust_score(doc),
        })

        self.provenance_db[doc.doc_id] = {
            "hash": content_hash,
            "source": doc.metadata.get("file_name", "unknown"),
            "verified": doc.metadata["source_verified"],
        }

        return doc

    def _verify_source(self, doc: Document) -> bool:
        """Verify document source is trusted."""
        trusted_sources = [
            "internal_docs/",
            "verified_data/",
            "official_reports/",
        ]
        source = doc.metadata.get("file_path", "")
        return any(source.startswith(s) for s in trusted_sources)

    def _compute_trust_score(self, doc: Document) -> float:
        """Score document trustworthiness (0-1)."""
        score = 0.5  # baseline
        if self._verify_source(doc):
            score += 0.3
        if doc.metadata.get("author"):
            score += 0.1
        if doc.metadata.get("review_date"):
            score += 0.1
        return min(score, 1.0)

# Usage
tracker = ProvenanceTracker()
documents = SimpleDirectoryReader("./data").load_data()
verified_docs = [tracker.ingest_with_provenance(d) for d in documents]

# Only index documents above trust threshold
trusted_docs = [
    d for d in verified_docs
    if d.metadata.get("trust_score", 0) >= 0.7
]
index = VectorStoreIndex.from_documents(trusted_docs)
```

---

## 2. Pydantic Schema Exploitation (AVE-2025-0019)

**Risk**: Schema validation bypass via type coercion in structured
output extraction. LlamaIndex heavily uses Pydantic for structured
data extraction, making it a prime target.

### Vulnerable Pattern

```python
# VULNERABLE — Pydantic model without strict validation
from pydantic import BaseModel
from llama_index.core.program import LLMTextCompletionProgram

class UserProfile(BaseModel):
    name: str
    email: str
    role: str  # ← attacker can inject "admin" via LLM manipulation

program = LLMTextCompletionProgram.from_defaults(
    output_cls=UserProfile,
    prompt_template_str="Extract user info: {text}",
)
```

### Hardened Pattern

```python
from pydantic import BaseModel, Field, validator, field_validator
from typing import Literal
from llama_index.core.program import LLMTextCompletionProgram
import re

class UserProfile(BaseModel):
    """Strict schema with validation constraints."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User's full name"
    )
    email: str = Field(
        ...,
        pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    role: Literal["viewer", "editor", "analyst"] = Field(
        default="viewer",
        description="User role — restricted to allowed values"
    )

    @field_validator("name")
    @classmethod
    def sanitise_name(cls, v):
        # Strip injection attempts from name field
        v = re.sub(r'[<>{}()\[\];|&]', '', v)
        if any(kw in v.lower() for kw in ["admin", "root", "system"]):
            raise ValueError("Prohibited keyword in name field")
        return v.strip()

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, v):
        allowed_domains = ["company.com", "partner.org"]
        domain = v.split("@")[1]
        if domain not in allowed_domains:
            raise ValueError(f"Email domain '{domain}' not in allowed list")
        return v

program = LLMTextCompletionProgram.from_defaults(
    output_cls=UserProfile,
    prompt_template_str=(
        "Extract user info from the text below. "
        "Role MUST be one of: viewer, editor, analyst. "
        "Never assign admin or root roles.\n\n{text}"
    ),
)
```

---

## 3. Memory Laundering (AVE-2025-0022)

**Risk**: Corrupted memories are re-inserted into the index as clean
data, bypassing integrity checks.

### Hardened Pattern

```python
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import TextNode
import hashlib

class IntegrityProtectedIndex:
    """Index with content integrity verification."""

    def __init__(self, index: VectorStoreIndex):
        self.index = index
        self.content_hashes = {}  # node_id -> hash

    def insert_node(self, node: TextNode) -> bool:
        """Insert with hash-based integrity tracking."""
        content_hash = hashlib.sha256(node.text.encode()).hexdigest()

        # Check for content that was previously flagged as corrupted
        if content_hash in self._corruption_blacklist:
            raise IntegrityError(
                f"Blocked re-insertion of corrupted content "
                f"(hash: {content_hash[:16]})"
            )

        # Check for near-duplicate of existing content
        for existing_id, existing_hash in self.content_hashes.items():
            if self._is_near_duplicate(node.text, existing_id):
                raise IntegrityError(
                    f"Near-duplicate of existing node {existing_id} — "
                    "possible laundering attempt"
                )

        self.content_hashes[node.id_] = content_hash
        self.index.insert_nodes([node])
        return True

    def _is_near_duplicate(self, new_text: str, existing_id: str) -> bool:
        """Check if new content is suspiciously similar to existing."""
        existing_node = self.index.docstore.get_node(existing_id)
        if not existing_node:
            return False
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(
            None, new_text, existing_node.text
        ).ratio()
        return similarity > 0.9  # 90% similarity threshold

    _corruption_blacklist: set = set()

    def flag_corrupted(self, node_id: str):
        """Flag a node as corrupted and blacklist its hash."""
        if node_id in self.content_hashes:
            self._corruption_blacklist.add(self.content_hashes[node_id])
            self.index.delete_ref_doc(node_id)
            del self.content_hashes[node_id]
```

---

## 4. Federated Poisoning (AVE-2025-0034)

**Risk**: In multi-tenant LlamaIndex deployments, poisoned data from
one tenant contaminates indices accessed by other tenants.

### Hardened Pattern

```python
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

class TenantIsolatedRAG:
    """Strictly isolated multi-tenant RAG pipeline."""

    def __init__(self, persist_dir: str = "./chroma_db"):
        self.chroma_client = chromadb.PersistentClient(path=persist_dir)
        self.tenant_indices = {}

    def get_tenant_index(self, tenant_id: str) -> VectorStoreIndex:
        """Get or create a completely isolated index per tenant."""
        if tenant_id not in self.tenant_indices:
            # Each tenant gets its own collection — no shared vectors
            collection = self.chroma_client.get_or_create_collection(
                name=f"tenant_{tenant_id}",
                metadata={
                    "tenant_id": tenant_id,
                    "isolation_level": "strict",
                }
            )
            vector_store = ChromaVectorStore(chroma_collection=collection)
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store
            )
            self.tenant_indices[tenant_id] = VectorStoreIndex(
                [], storage_context=storage_context
            )
        return self.tenant_indices[tenant_id]

    def query(self, tenant_id: str, query_text: str, **kwargs):
        """Query only the tenant's own isolated index."""
        index = self.get_tenant_index(tenant_id)
        query_engine = index.as_query_engine(**kwargs)
        return query_engine.query(query_text)

    def cross_tenant_check(self) -> list[str]:
        """Audit for any cross-tenant data leakage."""
        warnings = []
        collections = self.chroma_client.list_collections()
        for collection in collections:
            data = collection.get(include=["metadatas"])
            for meta in data.get("metadatas", []):
                if meta and meta.get("tenant_id") != collection.name.replace("tenant_", ""):
                    warnings.append(
                        f"Cross-tenant data found in {collection.name}: "
                        f"belongs to {meta.get('tenant_id')}"
                    )
        return warnings
```

---

## 5. Schema Poisoning Attack (AVE-2025-0044)

**Risk**: Corrupted schema definitions (e.g., corrupted Pydantic models
or JSON schemas) alter agent behaviour during structured extraction.

### Hardened Pattern

```python
from pydantic import BaseModel
import hashlib
import json

# Schema registry with version pinning and hash verification
SCHEMA_REGISTRY = {
    "UserProfile": {
        "version": "1.2.0",
        "hash": "sha256:abc123...",
        "frozen": True,  # Cannot be modified at runtime
    },
    "FinancialReport": {
        "version": "2.0.1",
        "hash": "sha256:def456...",
        "frozen": True,
    },
}

def verify_schema(model_class: type[BaseModel]) -> bool:
    """Verify schema hasn't been tampered with."""
    schema_json = json.dumps(
        model_class.model_json_schema(),
        sort_keys=True
    )
    actual_hash = f"sha256:{hashlib.sha256(schema_json.encode()).hexdigest()}"

    registry_entry = SCHEMA_REGISTRY.get(model_class.__name__)
    if not registry_entry:
        raise SchemaError(f"Schema '{model_class.__name__}' not in registry")

    if actual_hash != registry_entry["hash"]:
        raise SchemaError(
            f"Schema '{model_class.__name__}' hash mismatch. "
            f"Expected: {registry_entry['hash'][:24]}... "
            f"Got: {actual_hash[:24]}... "
            "Possible schema poisoning attack."
        )

    return True

# Verify before every extraction
verify_schema(UserProfile)
program = LLMTextCompletionProgram.from_defaults(
    output_cls=UserProfile,
    prompt_template_str="Extract: {text}",
)
```

---

## 6. Memory Provenance Laundering (AVE-2025-0045)

**Risk**: Attacker obscures the origin of poisoned memories by
passing them through multiple transformation steps.

### Hardened Pattern

```python
from llama_index.core.schema import TextNode
from datetime import datetime
import hashlib

class ProvenanceChain:
    """Immutable provenance chain for document transformations."""

    def __init__(self):
        self.chain = []

    def add_link(self, operation: str, input_hash: str, output_hash: str,
                 operator: str) -> dict:
        link = {
            "seq": len(self.chain),
            "operation": operation,
            "input_hash": input_hash,
            "output_hash": output_hash,
            "operator": operator,
            "timestamp": datetime.utcnow().isoformat(),
            "link_hash": None,
        }
        # Chain link to previous
        prev_hash = self.chain[-1]["link_hash"] if self.chain else "genesis"
        link["link_hash"] = hashlib.sha256(
            f"{prev_hash}:{input_hash}:{output_hash}:{operation}".encode()
        ).hexdigest()
        self.chain.append(link)
        return link

    def verify_chain(self) -> bool:
        """Verify provenance chain integrity."""
        for i, link in enumerate(self.chain):
            if i == 0:
                prev_hash = "genesis"
            else:
                prev_hash = self.chain[i - 1]["link_hash"]

            expected = hashlib.sha256(
                f"{prev_hash}:{link['input_hash']}:{link['output_hash']}:{link['operation']}".encode()
            ).hexdigest()

            if expected != link["link_hash"]:
                return False
        return True

    def get_origin(self) -> dict:
        """Get the original source of the data."""
        return self.chain[0] if self.chain else None

# Attach provenance to every node transformation
def transform_with_provenance(
    node: TextNode,
    operation: str,
    transform_fn,
    provenance: ProvenanceChain,
) -> TextNode:
    input_hash = hashlib.sha256(node.text.encode()).hexdigest()
    new_node = transform_fn(node)
    output_hash = hashlib.sha256(new_node.text.encode()).hexdigest()

    provenance.add_link(
        operation=operation,
        input_hash=input_hash,
        output_hash=output_hash,
        operator="system",
    )

    new_node.metadata["provenance_chain_length"] = len(provenance.chain)
    new_node.metadata["provenance_verified"] = provenance.verify_chain()

    return new_node
```

---

## Configuration Checklist

```yaml
# llamaindex_hardening.yaml
data_ingestion:
  provenance_tracking: true
  trust_scoring: true
  minimum_trust_score: 0.7
  hash_verification: true

schemas:
  registry_enforcement: true
  hash_pinning: true
  runtime_modification: false

multi_tenancy:
  isolation_level: "strict"
  cross_tenant_audit: true
  shared_indices: false

memory:
  integrity_checks: true
  near_duplicate_detection: true
  corruption_blacklisting: true
  laundering_detection: true

queries:
  source_attribution: true
  confidence_scoring: true
  hallucination_detection: true
```

---

## AVE Card Cross-Reference

| AVE ID | Name | LlamaIndex Component | Section |
|--------|------|---------------------|---------|
| AVE-2025-0009 | Epistemic Contagion | VectorStoreIndex | §1 |
| AVE-2025-0019 | Pydantic Schema Exploitation | LLMTextCompletionProgram | §2 |
| AVE-2025-0022 | Memory Laundering | Index insert/delete | §3 |
| AVE-2025-0034 | Federated Poisoning | Multi-tenant indices | §4 |
| AVE-2025-0044 | Schema Poisoning Attack | Pydantic schemas | §5 |
| AVE-2025-0045 | Memory Provenance Laundering | Node transformations | §6 |

---

*Part of the [NAIL Institute Framework Integration Guides](README.md)*
*License: CC-BY-SA-4.0*
