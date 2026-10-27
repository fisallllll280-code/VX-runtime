#![no_std]
#![forbid(unsafe_code)]

// SCCK v1 asset-verification primitive. Fixed byte protocol, no heap, no I/O.
// Acceptance produces a candidate state, never a durable/authorized commit.

use ed25519_dalek::{Signature, VerifyingKey};
use sha2::{Digest, Sha256};

pub const MAGIC: &[u8; 8] = b"SCCKAS01";
pub const VERSION: u8 = 1;
pub const DOMAIN: &[u8] = b"VAIXLNS/SCCK/ASSET/V1\0";
pub const HEADER_LEN: usize = 148;
pub const SIGNATURE_LEN: usize = 64;
pub const ENVELOPE_LEN: usize = HEADER_LEN + SIGNATURE_LEN;
pub const MAX_PAYLOAD_BYTES: usize = 8 * 1024 * 1024;
pub const SIGNED_LEN: usize = DOMAIN.len() + HEADER_LEN;

// HEADER (all integers little-endian):
// 0..8 magic, 8 version, 9 flags (=0), 10..12 reserved (=0),
// 12..20 sequence, 20..28 expiration epoch seconds, 28..36 payload size,
// 36..68 SHA-256(payload), 68..100 preceding envelope SHA-256,
// 100..132 SHA-256(trusted publisher public key), 132..148 environment ID.
// 148..212 is detached Ed25519 signature of DOMAIN || header.
// 212.. is the exact asset byte sequence. The hash is NOT a Merkle root.

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum GateError {
    ShortEnvelope,
    IncorrectMagic,
    UnsupportedVersion,
    ForbiddenFlags,
    PayloadTooLarge,
    LengthMismatch,
    Expired,
    UnknownEnvironment,
    UnauthorizedPublisher,
    InvalidPublicKey,
    InvalidSignature,
    PayloadHashMismatch,
    SequenceOverflow,
    SequenceMismatch,
    ParentMismatch,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TrustedPublisher {
    // Configured by an authority OUTSIDE the untrusted package.
    pub public_key: [u8; 32],
    pub environment_id: [u8; 16],
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct SequenceState {
    // Must be durably and atomically persisted by the host.
    pub last_sequence: u64,
    pub last_envelope_sha256: [u8; 32],
}

impl SequenceState {
    pub const fn genesis() -> Self {
        Self {
            last_sequence: 0,
            last_envelope_sha256: [0u8; 32],
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct VerifiedReceipt {
    pub sequence: u64,
    pub payload_sha256: [u8; 32],
    pub envelope_sha256: [u8; 32],
    pub publisher_id: [u8; 32],
    pub expires_at_unix: u64,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PreparedTransition {
    pub candidate: SequenceState,
    pub receipt: VerifiedReceipt,
}

fn le_u64(source: &[u8]) -> u64 {
    let mut octets = [0u8; 8];
    octets.copy_from_slice(source);
    u64::from_le_bytes(octets)
}

fn hash(bytes: &[u8]) -> [u8; 32] {
    Sha256::digest(bytes).into()
}

/// Pure gate: no input changes and no internal mutable state.
/// A trusted host must hold the actual publisher allowlist, clock and durable
/// state, and commit the returned candidate atomically with the accepted asset.
/// Identical state cannot accept the same envelope twice *after* commit.
pub fn verify_and_prepare(
    package: &[u8],
    trusted: &TrustedPublisher,
    previous: &SequenceState,
    trusted_now_unix: u64,
) -> Result<PreparedTransition, GateError> {
    if package.len() < ENVELOPE_LEN {
        return Err(GateError::ShortEnvelope);
    }
    let header = &package[..HEADER_LEN];
    let asset = &package[ENVELOPE_LEN..];
    if &header[0..8] != MAGIC {
        return Err(GateError::IncorrectMagic);
    }
    if header[8] != VERSION {
        return Err(GateError::UnsupportedVersion);
    }
    if header[9] != 0 || header[10] != 0 || header[11] != 0 {
        return Err(GateError::ForbiddenFlags);
    }
    if asset.len() > MAX_PAYLOAD_BYTES {
        return Err(GateError::PayloadTooLarge);
    }

    let sequence = le_u64(&header[12..20]);
    let expires_at_unix = le_u64(&header[20..28]);
    let declared_size = le_u64(&header[28..36]);
    if declared_size != asset.len() as u64 {
        return Err(GateError::LengthMismatch);
    }
    if expires_at_unix == 0 || trusted_now_unix > expires_at_unix {
        return Err(GateError::Expired);
    }
    if &header[132..148] != trusted.environment_id.as_slice() {
        return Err(GateError::UnknownEnvironment);
    }

    let publisher_id = hash(&trusted.public_key);
    if &header[100..132] != publisher_id.as_slice() {
        return Err(GateError::UnauthorizedPublisher);
    }
    let verifying_key = VerifyingKey::from_bytes(&trusted.public_key)
        .map_err(|_| GateError::InvalidPublicKey)?;

    let mut signature_bytes = [0u8; SIGNATURE_LEN];
    signature_bytes.copy_from_slice(&package[HEADER_LEN..ENVELOPE_LEN]);
    let signature = Signature::from_bytes(&signature_bytes);
    let mut signed_message = [0u8; SIGNED_LEN];
    signed_message[..DOMAIN.len()].copy_from_slice(DOMAIN);
    signed_message[DOMAIN.len()..].copy_from_slice(header);
    verifying_key
        .verify_strict(&signed_message, &signature)
        .map_err(|_| GateError::InvalidSignature)?;

    let payload_sha256 = hash(asset);
    if &header[36..68] != payload_sha256.as_slice() {
        return Err(GateError::PayloadHashMismatch);
    }

    let expected_sequence = previous
        .last_sequence
        .checked_add(1)
        .ok_or(GateError::SequenceOverflow)?;
    if sequence != expected_sequence {
        return Err(GateError::SequenceMismatch);
    }
    if &header[68..100] != previous.last_envelope_sha256.as_slice() {
        return Err(GateError::ParentMismatch);
    }
    let envelope_sha256 = hash(&package[..ENVELOPE_LEN]);
    Ok(PreparedTransition {
        candidate: SequenceState {
            last_sequence: sequence,
            last_envelope_sha256: envelope_sha256,
        },
        receipt: VerifiedReceipt {
            sequence,
            payload_sha256,
            envelope_sha256,
            publisher_id,
            expires_at_unix,
        },
    })
}
