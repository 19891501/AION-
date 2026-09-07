//! Macaroons délégués (Google 2014) — pure std.
//!
//! Chaîne HMAC : chaque caveat re-lie la signature précédente.
//! Atténuation hors ligne : on empile une contrainte, on ne peut pas l'enlever
//! ni l'élargir sans la clé racine.
//!
//! First-party : prédicats évalués par le vérificateur AION.
//! Third-party : structure présente ; `vid` lab = clé de caveat en hex
//! (en production, chiffrer `vid` vers le tiers).

use crate::mini_json::{dumps_compact_sorted, parse, Value};
use crate::sha256_hmac::{hex_decode, hex_encode, hmac_sha256};
use std::collections::BTreeMap;

#[derive(Clone, Debug, PartialEq)]
pub struct Caveat {
    pub cid: String,
    pub vid: Option<String>,
    pub cl: Option<String>,
}

impl Caveat {
    pub fn first_party(cid: impl Into<String>) -> Self {
        Self {
            cid: cid.into(),
            vid: None,
            cl: None,
        }
    }

    pub fn is_first_party(&self) -> bool {
        self.vid.as_deref().unwrap_or("").is_empty()
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct Macaroon {
    pub location: String,
    pub identifier: String,
    pub caveats: Vec<Caveat>,
    pub signature: [u8; 32],
}

#[derive(Clone, Debug, Default)]
pub struct Request {
    pub action: Option<String>,
    pub actor: Option<String>,
    pub target: Option<String>,
    pub amount: Option<f64>,
    pub now: f64,
    pub tau_hash: Option<String>,
    pub uses: u32,
}

#[derive(Debug, PartialEq)]
pub enum MacError {
    Signature,
    Predicate(String),
    Amplification(String),
    Json,
    Discharge,
    Encoding,
}

impl std::fmt::Display for MacError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            MacError::Signature => write!(f, "signature_invalide"),
            MacError::Predicate(p) => write!(f, "caveat_refuse:{p}"),
            MacError::Amplification(p) => write!(f, "amplification:{p}"),
            MacError::Json => write!(f, "json_invalide"),
            MacError::Discharge => write!(f, "discharge_manquant"),
            MacError::Encoding => write!(f, "encodage_invalide"),
        }
    }
}

fn hmac_key(sig: &[u8; 32], msg: &[u8]) -> [u8; 32] {
    hmac_sha256(sig, msg)
}

impl Macaroon {
    pub fn mint(root_key: &[u8], identifier: &str, location: &str) -> Self {
        let signature = hmac_sha256(root_key, identifier.as_bytes());
        Self {
            location: location.into(),
            identifier: identifier.into(),
            caveats: Vec::new(),
            signature,
        }
    }

    /// Empile un caveat first-party. Ne nécessite pas la clé racine.
    pub fn append_caveat(&mut self, cid: &str) {
        self.signature = hmac_key(&self.signature, cid.as_bytes());
        self.caveats.push(Caveat::first_party(cid));
    }

    /// Atténuation avec contrôle de non-amplification sur les prédicats numériques
    /// et d'égalité déjà présents.
    pub fn attenuate(&mut self, cid: &str) -> Result<(), MacError> {
        if let Some(why) = would_amplify(&self.caveats, cid) {
            return Err(MacError::Amplification(why));
        }
        self.append_caveat(cid);
        Ok(())
    }

    /// Third-party caveat. `caveat_key` est la clé avec laquelle le tiers minte
    /// le discharge. En lab, `vid` = hex(caveat_key).
    pub fn add_third_party(&mut self, location: &str, cid: &str, caveat_key: &[u8]) {
        let vid = hex_encode(caveat_key);
        let mut msg = vid.into_bytes();
        msg.extend_from_slice(cid.as_bytes());
        self.signature = hmac_key(&self.signature, &msg);
        self.caveats.push(Caveat {
            cid: cid.into(),
            vid: Some(hex_encode(caveat_key)),
            cl: Some(location.into()),
        });
    }

    pub fn verify(&self, root_key: &[u8], req: &Request) -> Result<(), MacError> {
        self.verify_with_discharges(root_key, req, &[])
    }

    pub fn verify_with_discharges(
        &self,
        root_key: &[u8],
        req: &Request,
        discharges: &[Macaroon],
    ) -> Result<(), MacError> {
        let mut sig = hmac_sha256(root_key, self.identifier.as_bytes());
        for c in &self.caveats {
            if c.is_first_party() {
                eval_predicate(&c.cid, req)?;
                sig = hmac_key(&sig, c.cid.as_bytes());
            } else {
                let vid = c.vid.as_deref().unwrap_or("");
                let key = hex_decode(vid).ok_or(MacError::Encoding)?;
                let discharge = discharges
                    .iter()
                    .find(|d| d.identifier == c.cid)
                    .ok_or(MacError::Discharge)?;
                discharge.verify(&key, req)?;
                let mut msg = vid.as_bytes().to_vec();
                msg.extend_from_slice(c.cid.as_bytes());
                sig = hmac_key(&sig, &msg);
            }
        }
        if sig != self.signature {
            return Err(MacError::Signature);
        }
        Ok(())
    }

    pub fn to_json(&self) -> String {
        let mut root = BTreeMap::new();
        root.insert("location".into(), Value::String(self.location.clone()));
        root.insert("identifier".into(), Value::String(self.identifier.clone()));
        let cav: Vec<Value> = self
            .caveats
            .iter()
            .map(|c| {
                let mut o = BTreeMap::new();
                o.insert("cid".into(), Value::String(c.cid.clone()));
                if let Some(v) = &c.vid {
                    o.insert("vid".into(), Value::String(v.clone()));
                }
                if let Some(l) = &c.cl {
                    o.insert("cl".into(), Value::String(l.clone()));
                }
                Value::Object(o)
            })
            .collect();
        root.insert("caveats".into(), Value::Array(cav));
        root.insert("signature".into(), Value::String(hex_encode(&self.signature)));
        dumps_compact_sorted(&root)
    }

    pub fn from_json(s: &str) -> Result<Self, MacError> {
        let v = parse(s.trim()).map_err(|_| MacError::Json)?;
        let o = v.as_object().ok_or(MacError::Json)?;
        let location = o
            .get("location")
            .and_then(|x| x.as_str())
            .unwrap_or("")
            .to_string();
        let identifier = o
            .get("identifier")
            .and_then(|x| x.as_str())
            .ok_or(MacError::Json)?
            .to_string();
        let sig_hex = o
            .get("signature")
            .and_then(|x| x.as_str())
            .ok_or(MacError::Json)?;
        let bytes = hex_decode(sig_hex).ok_or(MacError::Encoding)?;
        if bytes.len() != 32 {
            return Err(MacError::Encoding);
        }
        let mut signature = [0u8; 32];
        signature.copy_from_slice(&bytes);
        let mut caveats = Vec::new();
        if let Some(Value::Array(arr)) = o.get("caveats") {
            for item in arr {
                let co = item.as_object().ok_or(MacError::Json)?;
                let cid = co
                    .get("cid")
                    .and_then(|x| x.as_str())
                    .ok_or(MacError::Json)?
                    .to_string();
                let vid = co.get("vid").and_then(|x| x.as_str()).map(|s| s.to_string());
                let cl = co.get("cl").and_then(|x| x.as_str()).map(|s| s.to_string());
                caveats.push(Caveat { cid, vid, cl });
            }
        }
        Ok(Self {
            location,
            identifier,
            caveats,
            signature,
        })
    }
}

/// Bind a discharge to a root macaroon (prevents reuse on another root).
pub fn bind_discharge(root: &Macaroon, discharge: &Macaroon) -> Macaroon {
    let mut d = discharge.clone();
    d.signature = hmac_sha256(&root.signature, &discharge.signature);
    d
}

fn would_amplify(existing: &[Caveat], new_cid: &str) -> Option<String> {
    let Some(new_p) = parse_pred(new_cid) else {
        return None;
    };
    for c in existing {
        if !c.is_first_party() {
            continue;
        }
        let Some(old) = parse_pred(&c.cid) else {
            continue;
        };
        match (&old, &new_p) {
            (Pred::Le { field: f1, value: v1 }, Pred::Le { field: f2, value: v2 })
                if f1 == f2 && v2 > v1 =>
            {
                return Some(format!("{f2}<={v2} elargit {f1}<={v1}"));
            }
            (Pred::Lt { field: f1, value: v1 }, Pred::Lt { field: f2, value: v2 })
                if f1 == f2 && v2 > v1 =>
            {
                return Some(format!("{f2}<{v2} elargit {f1}<{v1}"));
            }
            (Pred::Eq { field: f1, value: a }, Pred::Eq { field: f2, value: b })
                if f1 == f2 && a != b =>
            {
                return Some(format!("{f2}={b} contredit {f1}={a}"));
            }
            _ => {}
        }
    }
    None
}

#[derive(Clone)]
enum Pred {
    Eq { field: String, value: String },
    Le { field: String, value: f64 },
    Lt { field: String, value: f64 },
    Prefix { field: String, value: String },
}

fn parse_pred(cid: &str) -> Option<Pred> {
    let s = cid.trim();
    if let Some((l, r)) = s.split_once("<=") {
        let v: f64 = r.trim().parse().ok()?;
        return Some(Pred::Le {
            field: l.trim().to_string(),
            value: v,
        });
    }
    if let Some((l, r)) = s.split_once('<') {
        let v: f64 = r.trim().parse().ok()?;
        return Some(Pred::Lt {
            field: l.trim().to_string(),
            value: v,
        });
    }
    if let Some((l, r)) = s.split_once('=') {
        let field = l.trim();
        let value = r.trim().to_string();
        if field.ends_with("_prefix") || field == "target_prefix" {
            let f = field.trim_end_matches("_prefix").trim_end_matches('_');
            let field = if field == "target_prefix" {
                "target".into()
            } else {
                f.to_string()
            };
            return Some(Pred::Prefix { field, value });
        }
        return Some(Pred::Eq {
            field: field.into(),
            value,
        });
    }
    None
}

fn eval_predicate(cid: &str, req: &Request) -> Result<(), MacError> {
    let pred = parse_pred(cid).ok_or_else(|| MacError::Predicate(cid.into()))?;
    let ok = match pred {
        Pred::Eq { field, value } => match field.as_str() {
            "action" => req.action.as_deref() == Some(value.as_str()),
            "actor" => req.actor.as_deref() == Some(value.as_str()),
            "target" => req.target.as_deref() == Some(value.as_str()),
            "tau" => req.tau_hash.as_deref() == Some(value.as_str()),
            "max_uses" => {
                let n: u32 = value.parse().unwrap_or(0);
                req.uses < n
            }
            _ => false,
        },
        Pred::Le { field, value } => match field.as_str() {
            "amount" => req.amount.map(|a| a <= value).unwrap_or(false),
            "expires" => req.now <= value,
            _ => false,
        },
        Pred::Lt { field, value } => match field.as_str() {
            "amount" => req.amount.map(|a| a < value).unwrap_or(false),
            "expires" => req.now < value,
            _ => false,
        },
        Pred::Prefix { field, value } => match field.as_str() {
            "target" => req
                .target
                .as_deref()
                .map(|t| t.starts_with(&value))
                .unwrap_or(false),
            _ => false,
        },
    };
    if ok {
        Ok(())
    } else {
        Err(MacError::Predicate(cid.into()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const KEY: &[u8] = b"root-secret-aion";

    fn pay(amount: f64) -> Request {
        Request {
            action: Some("transfer".into()),
            actor: Some("agent-b".into()),
            target: Some("iban-X".into()),
            amount: Some(amount),
            now: 1_700_000_000.0,
            tau_hash: None,
            uses: 0,
        }
    }

    #[test]
    fn mint_verify_empty() {
        let m = Macaroon::mint(KEY, "root-v0", "aion-gate");
        m.verify(KEY, &pay(1.0)).unwrap();
    }

    #[test]
    fn wrong_key_fails() {
        let m = Macaroon::mint(KEY, "root-v0", "aion-gate");
        assert_eq!(m.verify(b"other", &pay(1.0)), Err(MacError::Signature));
    }

    #[test]
    fn attenuation_without_root_key() {
        let mut m = Macaroon::mint(KEY, "root-v0", "aion-gate");
        m.append_caveat("amount <= 100");
        let json = m.to_json();
        let mut child = Macaroon::from_json(&json).unwrap();
        child.attenuate("amount <= 40").unwrap();
        child.attenuate("action = transfer").unwrap();
        child.verify(KEY, &pay(20.0)).unwrap();
        assert_eq!(
            child.verify(KEY, &pay(50.0)),
            Err(MacError::Predicate("amount <= 40".into()))
        );
    }

    #[test]
    fn cannot_widen_amount() {
        let mut m = Macaroon::mint(KEY, "root-v0", "aion-gate");
        m.append_caveat("amount <= 50");
        let err = m.attenuate("amount <= 10000").unwrap_err();
        match err {
            MacError::Amplification(_) => {}
            other => panic!("{other:?}"),
        }
    }

    #[test]
    fn cannot_strip_caveat() {
        let mut m = Macaroon::mint(KEY, "root-v0", "aion-gate");
        m.append_caveat("amount <= 50");
        m.append_caveat("action = transfer");
        let mut stripped = m.clone();
        stripped.caveats.pop();
        assert_eq!(stripped.verify(KEY, &pay(10.0)), Err(MacError::Signature));
    }

    #[test]
    fn cannot_swap_predicate() {
        let mut m = Macaroon::mint(KEY, "root-v0", "aion-gate");
        m.append_caveat("amount <= 50");
        let mut evil = m.clone();
        evil.caveats[0].cid = "amount <= 10000".into();
        assert_eq!(evil.verify(KEY, &pay(9999.0)), Err(MacError::Signature));
    }

    #[test]
    fn json_roundtrip() {
        let mut m = Macaroon::mint(KEY, "id", "loc");
        m.append_caveat("actor = sales");
        let m2 = Macaroon::from_json(&m.to_json()).unwrap();
        assert_eq!(m, m2);
    }

    #[test]
    fn target_prefix() {
        let mut m = Macaroon::mint(KEY, "root-v0", "aion-gate");
        m.append_caveat("target_prefix = iban-");
        m.verify(KEY, &pay(1.0)).unwrap();
        let mut bad = pay(1.0);
        bad.target = Some("swift-Z".into());
        assert!(m.verify(KEY, &bad).is_err());
    }

    #[test]
    fn expires() {
        let mut m = Macaroon::mint(KEY, "root-v0", "aion-gate");
        m.append_caveat("expires < 1700000100");
        m.verify(KEY, &pay(1.0)).unwrap();
        let mut late = pay(1.0);
        late.now = 1_800_000_000.0;
        assert!(m.verify(KEY, &late).is_err());
    }

    #[test]
    fn third_party_requires_discharge() {
        let mut root = Macaroon::mint(KEY, "root-v0", "aion-gate");
        let ck = b"compliance-key-32bytes___________";
        root.add_third_party("compliance", "kyc-ok", ck);
        assert_eq!(root.verify(KEY, &pay(1.0)), Err(MacError::Discharge));
        let discharge = Macaroon::mint(ck, "kyc-ok", "compliance");
        root.verify_with_discharges(KEY, &pay(1.0), &[discharge])
            .unwrap();
    }

    #[test]
    fn delegation_chain_a_to_b() {
        let mut root = Macaroon::mint(KEY, "human-policy", "aion");
        root.append_caveat("amount <= 100");
        root.append_caveat("action = transfer");
        let mut a = root.clone();
        a.attenuate("amount <= 40").unwrap();
        let mut b = a.clone();
        b.attenuate("target = iban-X").unwrap();
        b.verify(KEY, &pay(30.0)).unwrap();
        assert!(b.verify(KEY, &pay(41.0)).is_err());
        let mut other = pay(10.0);
        other.target = Some("iban-EVIL".into());
        assert!(b.verify(KEY, &other).is_err());
    }
}
