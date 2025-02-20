use check_cert::checker::certificate::{self, Config as CertConfig};

// Taken from `x509-parser`.
static DER: &[u8] = include_bytes!("../assets/IGC_A.der");

static SERIAL: &str = "39:11:45:10:94";
static SUBJECT: &str =
    "C=FR, ST=France, L=Paris, O=PM/SGDN, OU=DCSSI, CN=IGC/A, Email=igca@sgdn.pm.gouv.fr";
static ISSUER: &str = SUBJECT;
static SIG_ALG: &str = "RSA";
static PUBKEY_ALG: &str = "RSA";
static PUBKEY_SZ: usize = 2048;

fn s(s: &str) -> Option<String> {
    Some(String::from(s))
}

#[test]
fn test_cert_ok() {
    let out = certificate::check(
        DER,
        CertConfig::builder()
            .serial(s(SERIAL))
            .subject(s(SUBJECT))
            .issuer(s(ISSUER))
            .signature_algorithm(s(SIG_ALG))
            .pubkey_algorithm(s(PUBKEY_ALG))
            .pubkey_size(Some(PUBKEY_SZ))
            .build(),
    );
    assert_eq!(
        out.to_string(),
        format!(
            "OK - \
            Serial: {SERIAL}, \
            Subject: {SUBJECT}, \
            Issuer: {ISSUER}, \
            Signature algorithm: {SIG_ALG}, \
            Public key algorithm: {PUBKEY_ALG}, \
            Public key size: {PUBKEY_SZ}"
        )
    );
}

#[test]
fn test_cert_wrong_serial() {
    let serial = "01:02:03:04:05";
    let out = certificate::check(
        DER,
        CertConfig::builder()
            .serial(s(serial))
            .subject(s(SUBJECT))
            .issuer(s(ISSUER))
            .build(),
    );
    assert_eq!(
        out.to_string(),
        format!(
            "WARNING - \
            Serial is {SERIAL} but expected {serial} (!), \
            Subject: {SUBJECT}, \
            Issuer: {ISSUER}"
        )
    );
}
