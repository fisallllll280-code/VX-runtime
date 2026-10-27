use ed25519_dalek::{Signer, SigningKey};
use sha2::{Digest, Sha256};
use vx_scck_verifier::{
    verify_and_prepare, GateError, PreparedTransition, SequenceState, TrustedPublisher, DOMAIN,
    ENVELOPE_LEN, HEADER_LEN, MAGIC, MAX_PAYLOAD_BYTES, SIGNED_LEN, VERSION,
};

const NOW: u64 = 1_783_000_000;
const EXPIRES: u64 = NOW + 3600;

fn fixture() -> (SigningKey, TrustedPublisher, SequenceState) {
    // Deterministic PUBLIC test fixture. Never use this key for real assets.
    let signer = SigningKey::from_bytes(&[7u8; 32]);
    let trusted = TrustedPublisher {
        public_key: signer.verifying_key().to_bytes(),
        environment_id: *b"VAIXLNS-DEV-0001",
    };
    (signer, trusted, SequenceState::genesis())
}

fn sha256(bytes: &[u8]) -> [u8; 32] {
    Sha256::digest(bytes).into()
}

fn signed_package(
    signer: &SigningKey,
    trusted: &TrustedPublisher,
    parent: &SequenceState,
    seq: u64,
    expiry: u64,
    payload: &[u8],
) -> Vec<u8> {
    let mut header = [0u8; HEADER_LEN];
    header[0..8].copy_from_slice(MAGIC);
    header[8] = VERSION;
    header[12..20].copy_from_slice(&seq.to_le_bytes());
    header[20..28].copy_from_slice(&expiry.to_le_bytes());
    header[28..36].copy_from_slice(&(payload.len() as u64).to_le_bytes());
    header[36..68].copy_from_slice(&sha256(payload));
    header[68..100].copy_from_slice(&parent.last_envelope_sha256);
    header[100..132].copy_from_slice(&sha256(&trusted.public_key));
    header[132..148].copy_from_slice(&trusted.environment_id);
    let mut message = [0u8; SIGNED_LEN];
    message[..DOMAIN.len()].copy_from_slice(DOMAIN);
    message[DOMAIN.len()..].copy_from_slice(&header);
    let signature = signer.sign(&message).to_bytes();
    let mut full = Vec::with_capacity(ENVELOPE_LEN + payload.len());
    full.extend_from_slice(&header);
    full.extend_from_slice(&signature);
    full.extend_from_slice(payload);
    full
}

fn valid() -> (Vec<u8>, TrustedPublisher, SequenceState) {
    let (signer, trusted, previous) = fixture();
    (
        signed_package(&signer, &trusted, &previous, 1, EXPIRES, b"alpha"),
        trusted,
        previous,
    )
}

fn verified(pkg: &[u8], trusted: &TrustedPublisher, state: &SequenceState) -> PreparedTransition {
    verify_and_prepare(pkg, trusted, state, NOW).expect("test fixture must verify")
}

#[test]
fn accepts_correct_signature_content_and_chained_next_state() {
    let (package, trusted, previous) = valid();
    let first = verified(&package, &trusted, &previous);
    assert_eq!(first.candidate.last_sequence, 1);
    assert_eq!(first.receipt.payload_sha256, sha256(b"alpha"));
    assert_eq!(first.candidate.last_envelope_sha256, sha256(&package[..ENVELOPE_LEN]));
    let (signer, _, _) = fixture();
    let second_package = signed_package(&signer, &trusted, &first.candidate, 2, EXPIRES, b"beta");
    let second = verified(&second_package, &trusted, &first.candidate);
    assert_eq!(second.candidate.last_sequence, 2);
}

#[test]
fn rejects_tampered_payload_preserving_previous_state() {
    let (mut package, trusted, previous) = valid();
    *package.last_mut().unwrap() ^= 1;
    let snapshot = previous;
    assert_eq!(
        verify_and_prepare(&package, &trusted, &previous, NOW),
        Err(GateError::PayloadHashMismatch),
    );
    assert_eq!(previous, snapshot);
}

#[test]
fn rejects_invalid_signature() {
    let (mut package, trusted, previous) = valid();
    package[HEADER_LEN + 3] ^= 1;
    assert_eq!(
        verify_and_prepare(&package, &trusted, &previous, NOW),
        Err(GateError::InvalidSignature),
    );
}

#[test]
fn rejects_signed_metadata_mutation() {
    let (mut package, trusted, previous) = valid();
    package[20] ^= 1;
    assert_eq!(
        verify_and_prepare(&package, &trusted, &previous, NOW),
        Err(GateError::InvalidSignature),
    );
}

#[test]
fn rejects_foreign_publisher() {
    let (package, mut trusted, previous) = valid();
    trusted.public_key = SigningKey::from_bytes(&[9u8; 32]).verifying_key().to_bytes();
    assert_eq!(
        verify_and_prepare(&package, &trusted, &previous, NOW),
        Err(GateError::UnauthorizedPublisher),
    );
}

#[test]
fn rejects_wrong_environment() {
    let (package, mut trusted, previous) = valid();
    trusted.environment_id = *b"VAIXLNS-DEV-0002";
    assert_eq!(
        verify_and_prepare(&package, &trusted, &previous, NOW),
        Err(GateError::UnknownEnvironment),
    );
}

#[test]
fn rejects_replay_after_a_committed_sequence() {
    let (package, trusted, previous) = valid();
    let committed = verified(&package, &trusted, &previous).candidate;
    assert_eq!(
        verify_and_prepare(&package, &trusted, &committed, NOW),
        Err(GateError::SequenceMismatch),
    );
}

#[test]
fn rejects_a_signed_wrong_parent() {
    let (signer, trusted, previous) = fixture();
    let modified = SequenceState {
        last_sequence: previous.last_sequence,
        last_envelope_sha256: [9u8; 32],
    };
    let package = signed_package(&signer, &trusted, &modified, 1, EXPIRES, b"alpha");
    assert_eq!(
        verify_and_prepare(&package, &trusted, &previous, NOW),
        Err(GateError::ParentMismatch),
    );
}

#[test]
fn rejects_signed_sequence_gap() {
    let (signer, trusted, previous) = fixture();
    let package = signed_package(&signer, &trusted, &previous, 4, EXPIRES, b"alpha");
    assert_eq!(
        verify_and_prepare(&package, &trusted, &previous, NOW),
        Err(GateError::SequenceMismatch),
    );
}

#[test]
fn rejects_expired_even_if_signature_valid() {
    let (package, trusted, previous) = valid();
    assert_eq!(
        verify_and_prepare(&package, &trusted, &previous, EXPIRES + 1),
        Err(GateError::Expired),
    );
}

#[test]
fn rejects_zero_expiry() {
    let (signer, trusted, previous) = fixture();
    let pkg = signed_package(&signer, &trusted, &previous, 1, 0, b"alpha");
    assert_eq!(
        verify_and_prepare(&pkg, &trusted, &previous, NOW),
        Err(GateError::Expired),
    );
}

#[test]
fn rejects_wrong_declared_length() {
    let (mut package, trusted, previous) = valid();
    package.extend_from_slice(b"extra");
    assert_eq!(
        verify_and_prepare(&package, &trusted, &previous, NOW),
        Err(GateError::LengthMismatch),
    );
}

#[test]
fn rejects_short_package() {
    let (_, trusted, previous) = valid();
    assert_eq!(
        verify_and_prepare(b"small", &trusted, &previous, NOW),
        Err(GateError::ShortEnvelope),
    );
}

#[test]
fn rejects_wrong_magic_and_version() {
    let (mut package, trusted, previous) = valid();
    package[0] ^= 1;
    assert_eq!(
        verify_and_prepare(&package, &trusted, &previous, NOW),
        Err(GateError::IncorrectMagic),
    );
    package[0] ^= 1;
    package[8] = 2;
    assert_eq!(
        verify_and_prepare(&package, &trusted, &previous, NOW),
        Err(GateError::UnsupportedVersion),
    );
}

#[test]
fn rejects_nonzero_reserved_bytes() {
    let (mut package, trusted, previous) = valid();
    package[10] = 42;
    assert_eq!(
        verify_and_prepare(&package, &trusted, &previous, NOW),
        Err(GateError::ForbiddenFlags),
    );
}

#[test]
fn rejects_exhausted_sequence_number() {
    let (signer, trusted, _) = fixture();
    let parent = SequenceState { last_sequence: u64::MAX, last_envelope_sha256: [2; 32] };
    let package = signed_package(&signer, &trusted, &parent, 0, EXPIRES, b"alpha");
    assert_eq!(
        verify_and_prepare(&package, &trusted, &parent, NOW),
        Err(GateError::SequenceOverflow),
    );
}

#[test]
fn rejects_payload_over_size_cap() {
    let (signer, trusted, previous) = fixture();
    let huge = vec![17u8; MAX_PAYLOAD_BYTES + 1];
    let package = signed_package(&signer, &trusted, &previous, 1, EXPIRES, &huge);
    assert_eq!(
        verify_and_prepare(&package, &trusted, &previous, NOW),
        Err(GateError::PayloadTooLarge),
    );
}

#[test]
fn signature_does_not_automatically_change_canonical_state() {
    let (package, trusted, previous) = valid();
    let prepared = verified(&package, &trusted, &previous);
    assert_eq!(previous, SequenceState::genesis());
    assert_ne!(prepared.candidate, previous);
}
