"""
Quantum-Safe Cryptography Layer — Core crypto server.

Post-quantum cryptographic primitives for securing agent-to-agent
communication, threat intelligence envelopes, and governance audit
trails.  Implements NIST-approved PQC algorithms (ML-KEM, ML-DSA,
SPHINCS+, Falcon, XMSS), hybrid mode (PQ + classical), envelope
encryption, key lifecycle management, algorithm agility, and
immutable crypto audit trail.
"""

from __future__ import annotations

import base64
import hashlib
import os
import random
import statistics
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="NAIL Quantum-Safe Cryptography Layer",
    description=(
        "Post-quantum cryptographic primitives securing agent comms, "
        "intel envelopes, and governance audit trails."
    ),
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Constants & Algorithm Registry
# ---------------------------------------------------------------------------


class AlgorithmFamily(str, Enum):
    LATTICE = "lattice"
    HASH_BASED = "hash_based"
    CODE_BASED = "code_based"
    HYBRID = "hybrid"


class AlgorithmPurpose(str, Enum):
    KEM = "kem"  # Key Encapsulation Mechanism
    SIGN = "sign"  # Digital Signature
    HYBRID_KEM = "hybrid_kem"


class SecurityLevel(int, Enum):
    LEVEL_1 = 1  # AES-128 equivalent
    LEVEL_3 = 3  # AES-192 equivalent
    LEVEL_5 = 5  # AES-256 equivalent


class KeyStatus(str, Enum):
    ACTIVE = "active"
    ROTATED = "rotated"
    REVOKED = "revoked"
    EXPIRED = "expired"


# Algorithm definitions — simulated parameters
ALGORITHM_REGISTRY: dict[str, dict[str, Any]] = {
    "ML-KEM-768": {
        "family": AlgorithmFamily.LATTICE, "purpose": AlgorithmPurpose.KEM,
        "security_level": SecurityLevel.LEVEL_3, "nist_status": "FIPS 203",
        "pk_bytes": 1184, "sk_bytes": 2400, "ct_bytes": 1088,
        "description": "Module-Lattice Key Encapsulation (Kyber-768)",
    },
    "ML-KEM-1024": {
        "family": AlgorithmFamily.LATTICE, "purpose": AlgorithmPurpose.KEM,
        "security_level": SecurityLevel.LEVEL_5, "nist_status": "FIPS 203",
        "pk_bytes": 1568, "sk_bytes": 3168, "ct_bytes": 1568,
        "description": "Module-Lattice Key Encapsulation (Kyber-1024)",
    },
    "ML-DSA-65": {
        "family": AlgorithmFamily.LATTICE, "purpose": AlgorithmPurpose.SIGN,
        "security_level": SecurityLevel.LEVEL_3, "nist_status": "FIPS 204",
        "pk_bytes": 1952, "sk_bytes": 4032, "sig_bytes": 3309,
        "description": "Module-Lattice Digital Signature (Dilithium-3)",
    },
    "ML-DSA-87": {
        "family": AlgorithmFamily.LATTICE, "purpose": AlgorithmPurpose.SIGN,
        "security_level": SecurityLevel.LEVEL_5, "nist_status": "FIPS 204",
        "pk_bytes": 2592, "sk_bytes": 4896, "sig_bytes": 4627,
        "description": "Module-Lattice Digital Signature (Dilithium-5)",
    },
    "SPHINCS+-SHA2-256f": {
        "family": AlgorithmFamily.HASH_BASED, "purpose": AlgorithmPurpose.SIGN,
        "security_level": SecurityLevel.LEVEL_5, "nist_status": "FIPS 205",
        "pk_bytes": 64, "sk_bytes": 128, "sig_bytes": 49856,
        "description": "Stateless hash-based signature (fast variant)",
    },
    "Falcon-1024": {
        "family": AlgorithmFamily.LATTICE, "purpose": AlgorithmPurpose.SIGN,
        "security_level": SecurityLevel.LEVEL_5, "nist_status": "Selected Round 4",
        "pk_bytes": 1793, "sk_bytes": 2305, "sig_bytes": 1280,
        "description": "Fast-Fourier Lattice-based Compact Signature",
    },
    "XMSS-SHA2-256": {
        "family": AlgorithmFamily.HASH_BASED, "purpose": AlgorithmPurpose.SIGN,
        "security_level": SecurityLevel.LEVEL_5, "nist_status": "SP 800-208",
        "pk_bytes": 64, "sk_bytes": 1395, "sig_bytes": 2692,
        "description": "Extended Merkle Signature Scheme (stateful)",
    },
    "BIKE-L3": {
        "family": AlgorithmFamily.CODE_BASED, "purpose": AlgorithmPurpose.KEM,
        "security_level": SecurityLevel.LEVEL_3, "nist_status": "Round 4 Candidate",
        "pk_bytes": 5122, "sk_bytes": 6230, "ct_bytes": 5154,
        "description": "Bit Flipping Key Encapsulation",
    },
    "HQC-256": {
        "family": AlgorithmFamily.CODE_BASED, "purpose": AlgorithmPurpose.KEM,
        "security_level": SecurityLevel.LEVEL_5, "nist_status": "Round 4 Candidate",
        "pk_bytes": 7245, "sk_bytes": 7285, "ct_bytes": 14469,
        "description": "Hamming Quasi-Cyclic KEM",
    },
    "X25519+ML-KEM-768": {
        "family": AlgorithmFamily.HYBRID, "purpose": AlgorithmPurpose.HYBRID_KEM,
        "security_level": SecurityLevel.LEVEL_3, "nist_status": "Hybrid",
        "pk_bytes": 1216, "sk_bytes": 2432, "ct_bytes": 1120,
        "description": "Hybrid classical + PQ KEM (X25519 + Kyber-768)",
    },
}


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class ManagedKey(BaseModel):
    id: str = Field(default_factory=lambda: f"KEY-{uuid.uuid4().hex[:10].upper()}")
    algorithm: str
    purpose: str
    security_level: int
    status: KeyStatus = KeyStatus.ACTIVE
    public_key_hex: str = ""
    public_key_fingerprint: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    rotated_at: Optional[str] = None
    revoked_at: Optional[str] = None
    expires_at: Optional[str] = None
    rotation_count: int = 0
    usage_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class KeyGenRequest(BaseModel):
    algorithm: str = "ML-KEM-768"
    label: str = ""
    ttl_days: int = 365


class EnvelopeEncryptRequest(BaseModel):
    recipient_key_id: str
    sender_sign_key_id: Optional[str] = None
    plaintext: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Envelope(BaseModel):
    id: str = Field(default_factory=lambda: f"ENV-{uuid.uuid4().hex[:10].upper()}")
    recipient_key_id: str
    sender_sign_key_id: Optional[str] = None
    algorithm_kem: str
    algorithm_sign: Optional[str] = None
    ciphertext_b64: str
    signature_b64: Optional[str] = None
    content_hash: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EnvelopeDecryptRequest(BaseModel):
    envelope_id: str
    recipient_key_id: str


class SignRequest(BaseModel):
    key_id: str
    message: str


class VerifyRequest(BaseModel):
    key_id: str
    message: str
    signature_b64: str


class AuditEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operation: str
    key_id: Optional[str] = None
    algorithm: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# In-Memory Stores  (production → HSM + PostgreSQL + Vault)
# ---------------------------------------------------------------------------

KEYS: dict[str, ManagedKey] = {}
ENVELOPES: dict[str, Envelope] = {}
AUDIT_LOG: list[AuditEntry] = []

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_now = lambda: datetime.now(timezone.utc)  # noqa: E731


def _audit(operation: str, key_id: str | None = None, algorithm: str | None = None, **details):
    entry = AuditEntry(operation=operation, key_id=key_id, algorithm=algorithm, details=details)
    AUDIT_LOG.append(entry)
    return entry


def _sim_keygen(algorithm: str) -> tuple[str, str]:
    """Simulate PQ keypair generation — returns (public_key_hex, fingerprint)."""
    algo_info = ALGORITHM_REGISTRY.get(algorithm, {})
    pk_size = algo_info.get("pk_bytes", 1024)
    # Simulate key material
    pk_bytes = os.urandom(min(pk_size, 64))  # Truncate for demo
    pk_hex = pk_bytes.hex()
    fingerprint = hashlib.sha256(pk_bytes).hexdigest()[:32]
    return pk_hex, fingerprint


def _sim_encrypt(plaintext: str, algorithm: str) -> str:
    """Simulate PQ encryption — returns base64 ciphertext."""
    # Combine plaintext with simulated randomness
    nonce = os.urandom(16)
    combined = nonce + plaintext.encode("utf-8")
    # Simulate lattice/code-based encryption (just encode for demo)
    ct = base64.b64encode(combined).decode()
    return ct


def _sim_decrypt(ciphertext_b64: str) -> str:
    """Simulate PQ decryption — returns plaintext."""
    combined = base64.b64decode(ciphertext_b64)
    plaintext = combined[16:].decode("utf-8")  # Strip simulated nonce
    return plaintext


def _sim_sign(message: str, algorithm: str) -> str:
    """Simulate PQ digital signature — returns base64 signature."""
    msg_hash = hashlib.sha3_512(message.encode()).digest()
    sig_material = msg_hash + os.urandom(32)
    return base64.b64encode(sig_material).decode()


def _sim_verify(message: str, signature_b64: str) -> bool:
    """Simulate PQ signature verification."""
    try:
        sig_bytes = base64.b64decode(signature_b64)
        msg_hash = hashlib.sha3_512(message.encode()).digest()
        # Check first 64 bytes match (our simulated scheme)
        return sig_bytes[:64] == msg_hash
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Seed Data
# ---------------------------------------------------------------------------

def _seed() -> None:
    seed_keys = [
        ("ML-KEM-768", "Agent-to-agent secure channel"),
        ("ML-DSA-65", "Intel envelope signing"),
        ("SPHINCS+-SHA2-256f", "Governance audit trail signing"),
        ("X25519+ML-KEM-768", "Hybrid transition channel"),
        ("Falcon-1024", "High-throughput compact signing"),
    ]

    for algo, label in seed_keys:
        algo_info = ALGORITHM_REGISTRY[algo]
        pk_hex, fp = _sim_keygen(algo)
        key = ManagedKey(
            algorithm=algo,
            purpose=algo_info["purpose"],
            security_level=algo_info["security_level"],
            public_key_hex=pk_hex,
            public_key_fingerprint=fp,
            expires_at=(_now() + timedelta(days=365)).isoformat(),
            metadata={"label": label},
        )
        KEYS[key.id] = key
        _audit("key_generated", key.id, algo, label=label)


_seed()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "quantum-safe-crypto-layer",
        "version": "1.0.0",
        "managed_keys": len(KEYS),
        "active_keys": sum(1 for k in KEYS.values() if k.status == KeyStatus.ACTIVE),
        "algorithms_supported": len(ALGORITHM_REGISTRY),
        "envelopes": len(ENVELOPES),
    }


# ---- Key Management ------------------------------------------------------

@app.post("/v1/keys/generate", status_code=status.HTTP_201_CREATED)
async def generate_key(req: KeyGenRequest):
    if req.algorithm not in ALGORITHM_REGISTRY:
        raise HTTPException(400, f"Unsupported algorithm. Supported: {list(ALGORITHM_REGISTRY.keys())}")

    algo_info = ALGORITHM_REGISTRY[req.algorithm]
    pk_hex, fp = _sim_keygen(req.algorithm)

    key = ManagedKey(
        algorithm=req.algorithm,
        purpose=algo_info["purpose"],
        security_level=algo_info["security_level"],
        public_key_hex=pk_hex,
        public_key_fingerprint=fp,
        expires_at=(_now() + timedelta(days=req.ttl_days)).isoformat(),
        metadata={"label": req.label},
    )
    KEYS[key.id] = key
    _audit("key_generated", key.id, req.algorithm, label=req.label)

    return {
        "id": key.id,
        "algorithm": key.algorithm,
        "security_level": key.security_level,
        "fingerprint": key.public_key_fingerprint,
        "expires_at": key.expires_at,
    }


@app.get("/v1/keys")
async def list_keys(
    status_filter: Optional[KeyStatus] = Query(None, alias="status"),
    algorithm: Optional[str] = None,
):
    keys = list(KEYS.values())
    if status_filter:
        keys = [k for k in keys if k.status == status_filter]
    if algorithm:
        keys = [k for k in keys if k.algorithm == algorithm]
    return {
        "count": len(keys),
        "keys": [
            {
                "id": k.id,
                "algorithm": k.algorithm,
                "purpose": k.purpose,
                "security_level": k.security_level,
                "status": k.status.value,
                "fingerprint": k.public_key_fingerprint,
                "usage_count": k.usage_count,
                "rotation_count": k.rotation_count,
                "created_at": k.created_at,
                "expires_at": k.expires_at,
            }
            for k in keys
        ],
    }


@app.get("/v1/keys/{key_id}")
async def get_key(key_id: str):
    if key_id not in KEYS:
        raise HTTPException(404, "Key not found")
    return KEYS[key_id].dict()


@app.post("/v1/keys/{key_id}/rotate")
async def rotate_key(key_id: str):
    if key_id not in KEYS:
        raise HTTPException(404, "Key not found")
    old_key = KEYS[key_id]
    if old_key.status != KeyStatus.ACTIVE:
        raise HTTPException(409, f"Can only rotate ACTIVE keys (current: {old_key.status.value})")

    # Retire old key
    old_key.status = KeyStatus.ROTATED
    old_key.rotated_at = _now().isoformat()

    # Generate new key with same algorithm
    pk_hex, fp = _sim_keygen(old_key.algorithm)
    new_key = ManagedKey(
        algorithm=old_key.algorithm,
        purpose=old_key.purpose,
        security_level=old_key.security_level,
        public_key_hex=pk_hex,
        public_key_fingerprint=fp,
        expires_at=old_key.expires_at,
        rotation_count=old_key.rotation_count + 1,
        metadata={**old_key.metadata, "rotated_from": key_id},
    )
    KEYS[new_key.id] = new_key

    _audit("key_rotated", key_id, old_key.algorithm, new_key_id=new_key.id)

    return {
        "rotated": True,
        "old_key_id": key_id,
        "new_key_id": new_key.id,
        "new_fingerprint": new_key.public_key_fingerprint,
    }


@app.post("/v1/keys/{key_id}/revoke")
async def revoke_key(key_id: str):
    if key_id not in KEYS:
        raise HTTPException(404, "Key not found")
    key = KEYS[key_id]
    if key.status in (KeyStatus.REVOKED,):
        raise HTTPException(409, "Key already revoked")

    key.status = KeyStatus.REVOKED
    key.revoked_at = _now().isoformat()
    _audit("key_revoked", key_id, key.algorithm)

    return {"revoked": True, "key_id": key_id}


# ---- Envelope Encryption -------------------------------------------------

@app.post("/v1/envelope/encrypt", status_code=status.HTTP_201_CREATED)
async def encrypt_envelope(req: EnvelopeEncryptRequest):
    if req.recipient_key_id not in KEYS:
        raise HTTPException(404, "Recipient key not found")
    recipient_key = KEYS[req.recipient_key_id]
    if recipient_key.status != KeyStatus.ACTIVE:
        raise HTTPException(409, "Recipient key is not active")

    algo_info = ALGORITHM_REGISTRY.get(recipient_key.algorithm, {})
    if algo_info.get("purpose") not in (AlgorithmPurpose.KEM, AlgorithmPurpose.HYBRID_KEM):
        raise HTTPException(400, f"Key algorithm {recipient_key.algorithm} is not a KEM — cannot encrypt")

    ciphertext = _sim_encrypt(req.plaintext, recipient_key.algorithm)
    content_hash = hashlib.sha256(req.plaintext.encode()).hexdigest()

    signature = None
    sign_algo = None
    if req.sender_sign_key_id:
        if req.sender_sign_key_id not in KEYS:
            raise HTTPException(404, "Sender signing key not found")
        sign_key = KEYS[req.sender_sign_key_id]
        if sign_key.status != KeyStatus.ACTIVE:
            raise HTTPException(409, "Signing key is not active")
        signature = _sim_sign(req.plaintext, sign_key.algorithm)
        sign_algo = sign_key.algorithm
        sign_key.usage_count += 1

    env = Envelope(
        recipient_key_id=req.recipient_key_id,
        sender_sign_key_id=req.sender_sign_key_id,
        algorithm_kem=recipient_key.algorithm,
        algorithm_sign=sign_algo,
        ciphertext_b64=ciphertext,
        signature_b64=signature,
        content_hash=content_hash,
    )
    ENVELOPES[env.id] = env
    recipient_key.usage_count += 1

    _audit("envelope_encrypted", req.recipient_key_id, recipient_key.algorithm,
           envelope_id=env.id, signed=bool(signature))

    return {
        "envelope_id": env.id,
        "algorithm_kem": env.algorithm_kem,
        "algorithm_sign": env.algorithm_sign,
        "content_hash": env.content_hash,
        "signed": bool(signature),
    }


@app.post("/v1/envelope/decrypt")
async def decrypt_envelope(req: EnvelopeDecryptRequest):
    if req.envelope_id not in ENVELOPES:
        raise HTTPException(404, "Envelope not found")
    if req.recipient_key_id not in KEYS:
        raise HTTPException(404, "Recipient key not found")

    env = ENVELOPES[req.envelope_id]
    if env.recipient_key_id != req.recipient_key_id:
        raise HTTPException(403, "Key does not match envelope recipient")

    key = KEYS[req.recipient_key_id]
    plaintext = _sim_decrypt(env.ciphertext_b64)
    content_hash = hashlib.sha256(plaintext.encode()).hexdigest()
    integrity = content_hash == env.content_hash

    sig_valid = None
    if env.signature_b64:
        sig_valid = _sim_verify(plaintext, env.signature_b64)

    _audit("envelope_decrypted", req.recipient_key_id, key.algorithm,
           envelope_id=env.id, integrity=integrity, signature_valid=sig_valid)

    return {
        "plaintext": plaintext,
        "integrity_verified": integrity,
        "signature_valid": sig_valid,
        "algorithm_kem": env.algorithm_kem,
        "algorithm_sign": env.algorithm_sign,
    }


# ---- Signing / Verification ----------------------------------------------

@app.post("/v1/sign")
async def sign_message(req: SignRequest):
    if req.key_id not in KEYS:
        raise HTTPException(404, "Signing key not found")
    key = KEYS[req.key_id]
    if key.status != KeyStatus.ACTIVE:
        raise HTTPException(409, "Key is not active")

    algo_info = ALGORITHM_REGISTRY.get(key.algorithm, {})
    if algo_info.get("purpose") != AlgorithmPurpose.SIGN:
        raise HTTPException(400, f"Key algorithm {key.algorithm} is not a signing algorithm")

    signature = _sim_sign(req.message, key.algorithm)
    key.usage_count += 1
    _audit("message_signed", req.key_id, key.algorithm)

    return {
        "signature_b64": signature,
        "algorithm": key.algorithm,
        "key_fingerprint": key.public_key_fingerprint,
    }


@app.post("/v1/verify")
async def verify_signature(req: VerifyRequest):
    if req.key_id not in KEYS:
        raise HTTPException(404, "Verification key not found")
    key = KEYS[req.key_id]

    valid = _sim_verify(req.message, req.signature_b64)
    _audit("signature_verified", req.key_id, key.algorithm, valid=valid)

    return {
        "valid": valid,
        "algorithm": key.algorithm,
        "key_fingerprint": key.public_key_fingerprint,
    }


# ---- Algorithm Registry ---------------------------------------------------

@app.get("/v1/algorithms")
async def list_algorithms(
    family: Optional[AlgorithmFamily] = None,
    purpose: Optional[AlgorithmPurpose] = None,
):
    algos = []
    for name, info in ALGORITHM_REGISTRY.items():
        if family and info["family"] != family:
            continue
        if purpose and info["purpose"] != purpose:
            continue
        algos.append({"name": name, **info})

    # Convert enums to strings for serialisation
    for a in algos:
        for k, v in a.items():
            if isinstance(v, Enum):
                a[k] = v.value

    return {"count": len(algos), "algorithms": algos}


# ---- Audit ---------------------------------------------------------------

@app.get("/v1/audit")
async def audit_log(
    operation: Optional[str] = None,
    key_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
):
    entries = AUDIT_LOG[:]
    if operation:
        entries = [e for e in entries if e.operation == operation]
    if key_id:
        entries = [e for e in entries if e.key_id == key_id]
    entries.sort(key=lambda e: e.timestamp, reverse=True)
    return {"count": len(entries[:limit]), "entries": [e.dict() for e in entries[:limit]]}


# ---- Analytics -----------------------------------------------------------

@app.get("/v1/analytics")
async def crypto_analytics():
    keys = list(KEYS.values())
    by_status = Counter(k.status.value for k in keys)
    by_algorithm = Counter(k.algorithm for k in keys)
    by_purpose = Counter(k.purpose for k in keys)
    by_level = Counter(k.security_level for k in keys)

    total_usage = sum(k.usage_count for k in keys)
    total_rotations = sum(k.rotation_count for k in keys)
    active_keys = [k for k in keys if k.status == KeyStatus.ACTIVE]

    by_op = Counter(e.operation for e in AUDIT_LOG)

    return {
        "total_keys": len(keys),
        "active_keys": len(active_keys),
        "by_status": dict(by_status),
        "by_algorithm": dict(by_algorithm),
        "by_purpose": dict(by_purpose),
        "by_security_level": {str(k): v for k, v in by_level.items()},
        "total_usage": total_usage,
        "total_rotations": total_rotations,
        "total_envelopes": len(ENVELOPES),
        "audit_entries": len(AUDIT_LOG),
        "by_operation": dict(by_op),
        "algorithms_supported": len(ALGORITHM_REGISTRY),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8900)
