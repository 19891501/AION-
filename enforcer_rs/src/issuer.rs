//! AION Issuer (Rust, pure std) — signe, ne mute jamais le monde.
mod mini_json;
mod sha256_hmac;

use mini_json::{dumps_compact_sorted, parse, Value};
use sha256_hmac::{hex_encode, hmac_sha256, sha256};
use std::collections::BTreeMap;
use std::env;
use std::io::{self, Read};
use std::time::{SystemTime, UNIX_EPOCH};

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

fn main() {
    let secret = match env::var("AION_ENFORCER_SECRET") {
        Ok(s) if !s.is_empty() => s,
        _ => {
            println!("{{\"error\":\"secret_absent\"}}");
            std::process::exit(1);
        }
    };
    let policy = env::var("AION_POLICY_HASH").unwrap_or_else(|_| "policy-v0".into());

    let mut input = String::new();
    if let Some(arg) = env::args().nth(1) {
        input = arg;
    } else {
        let _ = io::stdin().read_to_string(&mut input);
    }
    let req = match parse(input.trim()) {
        Ok(v) => v,
        Err(_) => {
            println!("{{\"error\":\"json_invalide\"}}");
            std::process::exit(1);
        }
    };
    let tau = match req.get("transition").and_then(|v| v.as_object()) {
        Some(o) => o,
        None => {
            println!("{{\"error\":\"json_invalide\"}}");
            std::process::exit(1);
        }
    };
    let ttl = req.get("ttl_sec").and_then(|v| v.as_f64()).unwrap_or(60.0);
    let th = hex_encode(&sha256(transition_canonical(tau).as_bytes()));
    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs_f64();
    let exp = now + ttl;
    let token_id = {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        let mut h = DefaultHasher::new();
        now.to_bits().hash(&mut h);
        std::process::id().hash(&mut h);
        format!("{:016x}{:016x}", h.finish(), (now * 1e6) as u64)
    };
    let msg = format!("{}|{}|{}|{}", token_id, th, exp, policy);
    let sig = hex_encode(&hmac_sha256(secret.as_bytes(), msg.as_bytes()));

    let mut auth = BTreeMap::new();
    auth.insert("token_id".into(), Value::String(token_id));
    auth.insert("transition_hash".into(), Value::String(th));
    auth.insert("issued_at".into(), Value::Number(now));
    auth.insert("expires_at".into(), Value::Number(exp));
    auth.insert("policy_hash".into(), Value::String(policy));
    auth.insert("signature".into(), Value::String(sig));
    let mut out = BTreeMap::new();
    out.insert("auth".into(), Value::Object(auth));
    println!("{}", dumps_compact_sorted(&out));
}
