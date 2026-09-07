//! CLI macaroons : mint | caveat | verify
//!
//!   AION_MACAROON_KEY=... aion-macaroon mint root-v0 aion-gate
//!   aion-macaroon caveat "amount <= 50" < macaroon.json
//!   aion-macaroon verify '{"macaroon":{...},"context":{"action":"transfer","amount":20}}'

use aion_enforcer::macaroon::{Macaroon, Request};
use aion_enforcer::mini_json::{dumps_compact_sorted, parse, Value};
use std::collections::BTreeMap;
use std::env;
use std::io::{self, Read};

fn key() -> Vec<u8> {
    env::var("AION_MACAROON_KEY")
        .or_else(|_| env::var("AION_ENFORCER_SECRET"))
        .unwrap_or_default()
        .into_bytes()
}

fn fail(reason: &str) -> ! {
    let mut o = BTreeMap::new();
    o.insert("ok".into(), Value::Bool(false));
    o.insert("reason".into(), Value::String(reason.into()));
    println!("{}", dumps_compact_sorted(&o));
    std::process::exit(1);
}

fn stdin_s() -> String {
    let mut s = String::new();
    let _ = io::stdin().read_to_string(&mut s);
    s
}

fn main() {
    let mut args = env::args().skip(1);
    let cmd = args.next().unwrap_or_default();
    match cmd.as_str() {
        "mint" => {
            let k = key();
            if k.is_empty() {
                fail("secret_absent");
            }
            let id = args.next().unwrap_or_else(|| "root-v0".into());
            let loc = args.next().unwrap_or_else(|| "aion-gate".into());
            let m = Macaroon::mint(&k, &id, &loc);
            println!("{}", m.to_json());
        }
        "caveat" => {
            let pred = args.next().unwrap_or_default();
            if pred.is_empty() {
                fail("caveat_absent");
            }
            let mut m = match Macaroon::from_json(&stdin_s()) {
                Ok(m) => m,
                Err(e) => fail(&e.to_string()),
            };
            if let Err(e) = m.attenuate(&pred) {
                fail(&e.to_string());
            }
            println!("{}", m.to_json());
        }
        "verify" => {
            let k = key();
            if k.is_empty() {
                fail("secret_absent");
            }
            let raw = args.next().unwrap_or_else(stdin_s);
            let v = parse(raw.trim()).unwrap_or_else(|_| fail("json_invalide"));
            let mac_json = if let Some(obj) = v.get("macaroon") {
                if let Value::Object(o) = obj {
                    dumps_compact_sorted(o)
                } else {
                    fail("json_invalide")
                }
            } else if v.get("signature").is_some() {
                raw
            } else {
                fail("json_invalide")
            };
            let m = Macaroon::from_json(&mac_json).unwrap_or_else(|e| fail(&e.to_string()));
            let ctx = v.get("context").and_then(|c| c.as_object());
            let req = Request {
                action: ctx
                    .and_then(|c| c.get("action"))
                    .and_then(|x| x.as_str())
                    .map(|s| s.to_string()),
                actor: ctx
                    .and_then(|c| c.get("actor"))
                    .and_then(|x| x.as_str())
                    .map(|s| s.to_string()),
                target: ctx
                    .and_then(|c| c.get("target"))
                    .and_then(|x| x.as_str())
                    .map(|s| s.to_string()),
                amount: ctx.and_then(|c| c.get("amount")).and_then(|x| x.as_f64()),
                now: ctx
                    .and_then(|c| c.get("now"))
                    .and_then(|x| x.as_f64())
                    .unwrap_or(0.0),
                tau_hash: ctx
                    .and_then(|c| c.get("tau"))
                    .and_then(|x| x.as_str())
                    .map(|s| s.to_string()),
                uses: ctx
                    .and_then(|c| c.get("uses"))
                    .and_then(|x| x.as_f64())
                    .unwrap_or(0.0) as u32,
            };
            match m.verify(&k, &req) {
                Ok(()) => {
                    let mut o = BTreeMap::new();
                    o.insert("ok".into(), Value::Bool(true));
                    o.insert("reason".into(), Value::String("authorized".into()));
                    println!("{}", dumps_compact_sorted(&o));
                }
                Err(e) => fail(&e.to_string()),
            }
        }
        _ => {
            eprintln!("usage: aion-macaroon mint|caveat|verify");
            std::process::exit(2);
        }
    }
}
