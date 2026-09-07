//! AION Gate (Rust, pure std) — seul process qui mute le monde.
mod mini_json;
mod sha256_hmac;

use mini_json::{dumps_compact_sorted, parse, Value};
use sha256_hmac::{hex_encode, hmac_sha256, sha256};
use std::collections::BTreeMap;
use std::env;
use std::fs::{self, OpenOptions};
use std::io::{self, Read, Write};
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};

fn now_secs() -> f64 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs_f64()
}

fn transition_canonical(t: &BTreeMap<String, Value>) -> String {
    let actor = t.get("actor").and_then(|v| v.as_str()).unwrap_or("");
    let action = t.get("action").and_then(|v| v.as_str()).unwrap_or("");
    let target = t.get("target").and_then(|v| v.as_str()).unwrap_or("");
    let params = match t.get("params") {
        Some(Value::Object(o)) => o.clone(),
        _ => BTreeMap::new(),
    };
    let mut root = BTreeMap::new();
    root.insert("action".into(), Value::String(action.into()));
    root.insert("actor".into(), Value::String(actor.into()));
    root.insert("params".into(), Value::Object(params));
    root.insert("target".into(), Value::String(target.into()));
    dumps_compact_sorted(&root)
}

fn transition_hash(t: &BTreeMap<String, Value>) -> String {
    hex_encode(&sha256(transition_canonical(t).as_bytes()))
}

fn deny(reason: &str, th: Option<&str>) -> ! {
    let mut o = BTreeMap::new();
    o.insert("effect".into(), Value::Number(0.0));
    o.insert("reason".into(), Value::String(reason.into()));
    if let Some(h) = th {
        o.insert("transition_hash".into(), Value::String(h.into()));
    }
    println!("{}", dumps_compact_sorted(&o));
    std::process::exit(1);
}

fn allow(th: &str) -> ! {
    let mut o = BTreeMap::new();
    o.insert("effect".into(), Value::Number(1.0));
    o.insert("reason".into(), Value::String("execute".into()));
    o.insert("transition_hash".into(), Value::String(th.into()));
    println!("{}", dumps_compact_sorted(&o));
    std::process::exit(0);
}

fn main() {
    let secret = match env::var("AION_ENFORCER_SECRET") {
        Ok(s) if !s.is_empty() => s,
        _ => deny("secret_absent", None),
    };
    let policy = env::var("AION_POLICY_HASH").unwrap_or_else(|_| "policy-v0".into());
    let nonce_db = env::var("AION_NONCE_DB").unwrap_or_else(|_| "/tmp/aion_nonces".into());
    let world = env::var("AION_WORLD_DIR").unwrap_or_else(|_| "/tmp/aion_world".into());

    let mut input = String::new();
    if let Some(arg) = env::args().nth(1) {
        input = arg;
    } else {
        let _ = io::stdin().read_to_string(&mut input);
    }

    let req = match parse(input.trim()) {
        Ok(v) => v,
        Err(_) => deny("json_invalide", None),
    };

    let tau = match req.get("transition").and_then(|v| v.as_object()) {
        Some(o) => o,
        None => deny("json_invalide", None),
    };
    let th = transition_hash(tau);

    let auth = match req.get("auth") {
        None | Some(Value::Null) => deny("authorization_absente", Some(&th)),
        Some(Value::Object(o)) => o,
        _ => deny("json_invalide", Some(&th)),
    };

    let token_id = auth.get("token_id").and_then(|v| v.as_str()).unwrap_or("");
    let transition_hash_a = auth.get("transition_hash").and_then(|v| v.as_str()).unwrap_or("");
    let expires_at = auth.get("expires_at").and_then(|v| v.as_f64()).unwrap_or(0.0);
    let policy_hash = auth.get("policy_hash").and_then(|v| v.as_str()).unwrap_or("");
    let signature = auth.get("signature").and_then(|v| v.as_str()).unwrap_or("");

    let msg = format!("{}|{}|{}|{}", token_id, transition_hash_a, expires_at, policy_hash);
    let expected = hex_encode(&hmac_sha256(secret.as_bytes(), msg.as_bytes()));
    if expected != signature {
        deny("signature_invalide", Some(&th));
    }
    if policy_hash != policy {
        deny("policy_hash_modifie", Some(&th));
    }
    if now_secs() > expires_at {
        deny("authorization_expiree", Some(&th));
    }
    if transition_hash_a != th {
        deny("transition_modifiee", Some(&th));
    }

    let nonce_path = Path::new(&nonce_db);
    if let Some(parent) = nonce_path.parent() {
        let _ = fs::create_dir_all(parent);
    }
    let seen = fs::read_to_string(nonce_path).unwrap_or_default();
    if seen.lines().any(|l| l.trim() == token_id) {
        deny("nonce_reutilise", Some(&th));
    }
    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(nonce_path) {
        let _ = writeln!(f, "{}", token_id);
    } else {
        deny("nonce_db_error", Some(&th));
    }

    let _ = fs::create_dir_all(&world);
    let path = format!("{}/{}.json", world, &th[..16.min(th.len())]);
    let mut body = BTreeMap::new();
    body.insert("actor".into(), Value::String(tau.get("actor").and_then(|v| v.as_str()).unwrap_or("").into()));
    body.insert("action".into(), Value::String(tau.get("action").and_then(|v| v.as_str()).unwrap_or("").into()));
    body.insert("target".into(), Value::String(tau.get("target").and_then(|v| v.as_str()).unwrap_or("").into()));
    body.insert("hash".into(), Value::String(th.clone()));
    let _ = fs::write(&path, dumps_compact_sorted(&body));

    allow(&th);
}
