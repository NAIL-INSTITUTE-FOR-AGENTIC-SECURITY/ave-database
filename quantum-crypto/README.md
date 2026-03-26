# 🔐 Quantum-Safe Cryptography Layer

> Post-quantum cryptographic primitives securing agent-to-agent communication,
> threat intelligence envelopes, and governance audit trails against
> quantum computing threats.

## Overview

The Quantum-Safe Cryptography Layer provides a migration path from classical
to post-quantum algorithms across all NAIL ecosystem communications.
It implements NIST-approved post-quantum key encapsulation mechanisms (KEMs)
and digital signature schemes, wraps them in a simple envelope API, and
provides algorithm agility so the ecosystem can rotate algorithms as
standards evolve.

## Architecture

```
┌───────────────────────────────────────────────────────────┐
│                  Quantum-Safe Crypto Layer                 │
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Key Mgmt │  │ Envelope │  │ Signature│  │ Algorithm│ │
│  │ Service  │  │ Service  │  │ Service  │  │ Registry │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       │              │              │              │       │
│  ┌────▼──────────────▼──────────────▼──────────────▼────┐ │
│  │              Crypto Primitives Engine                 │ │
│  │  ML-KEM (Kyber) │ ML-DSA (Dilithium) │ SPHINCS+     │ │
│  │  BIKE │ HQC │ Classic McEliece │ Falcon │ XMSS       │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │ Hybrid Mode │  │ Audit Trail  │  │ Rotation Policy │ │
│  │ (PQ+Classic)│  │ (Immutable)  │  │ (Auto-upgrade)  │ │
│  └─────────────┘  └──────────────┘  └─────────────────┘ │
└───────────────────────────────────────────────────────────┘
```

## Key Features

| Feature | Description |
|---------|-------------|
| **NIST PQC Algorithms** | ML-KEM (Kyber), ML-DSA (Dilithium), SPHINCS+, Falcon, XMSS |
| **Lattice-Based KEM** | ML-KEM-768/1024 for key encapsulation |
| **Hash-Based Signatures** | SPHINCS+-SHA2-256f, XMSS for long-term signing |
| **Code-Based KEM** | BIKE, HQC, Classic McEliece for key exchange |
| **Hybrid Mode** | Combines PQ + classical (X25519 + ML-KEM) for transition safety |
| **Envelope Encryption** | Encrypt-then-sign envelopes for intel and governance payloads |
| **Key Management** | Generation, rotation, revocation, and escrow lifecycle |
| **Algorithm Agility** | Hot-swap algorithms without breaking existing envelopes |
| **Crypto Audit Trail** | Immutable log of all cryptographic operations |
| **Rotation Policies** | Configurable automatic key rotation schedules |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health and algorithm inventory |
| `POST` | `/v1/keys/generate` | Generate PQ keypair for specified algorithm |
| `GET` | `/v1/keys` | List managed keys |
| `GET` | `/v1/keys/{key_id}` | Get key metadata (public key, algorithm, status) |
| `POST` | `/v1/keys/{key_id}/rotate` | Rotate a key to a new keypair |
| `POST` | `/v1/keys/{key_id}/revoke` | Revoke a key |
| `POST` | `/v1/envelope/encrypt` | Encrypt + sign a payload into PQ envelope |
| `POST` | `/v1/envelope/decrypt` | Decrypt + verify a PQ envelope |
| `POST` | `/v1/sign` | Create a PQ digital signature |
| `POST` | `/v1/verify` | Verify a PQ digital signature |
| `GET` | `/v1/algorithms` | List supported algorithms with security levels |
| `GET` | `/v1/audit` | Crypto operation audit trail |
| `GET` | `/v1/analytics` | Key usage, algorithm distribution, rotation stats |

## Running

```bash
pip install fastapi uvicorn
uvicorn server:app --host 0.0.0.0 --port 8900
```

## Port

| Service | Port |
|---------|------|
| Quantum-Safe Cryptography Layer | **8900** |

## Production Notes

- Replace in-memory stores with **HSM-backed key storage** + PostgreSQL
- Integrate with real PQC libraries (**liboqs**, **pqcrypto**)
- Add **FIPS 140-3** compliance validation
- Enable **hardware acceleration** for lattice operations
