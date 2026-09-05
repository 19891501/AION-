//! Minimal JSON subset for AION gate/issuer (objects, strings, numbers, null, bool).
use std::collections::BTreeMap;

#[derive(Clone, Debug)]
pub enum Value {
    Null,
    Bool(bool),
    Number(f64),
    String(String),
    Object(BTreeMap<String, Value>),
}

impl Value {
    pub fn as_str(&self) -> Option<&str> {
        match self {
            Value::String(s) => Some(s),
            _ => None,
        }
    }
    pub fn as_f64(&self) -> Option<f64> {
        match self {
            Value::Number(n) => Some(*n),
            _ => None,
        }
    }
    pub fn as_object(&self) -> Option<&BTreeMap<String, Value>> {
        match self {
            Value::Object(o) => Some(o),
            _ => None,
        }
    }
    pub fn get(&self, k: &str) -> Option<&Value> {
        self.as_object()?.get(k)
    }
}

pub fn parse(input: &str) -> Result<Value, String> {
    let mut p = Parser {
        s: input.trim().as_bytes(),
        i: 0,
    };
    p.parse_value()
}

struct Parser<'a> {
    s: &'a [u8],
    i: usize,
}

impl<'a> Parser<'a> {
    fn peek(&self) -> Option<u8> {
        self.s.get(self.i).copied()
    }
    fn bump(&mut self) {
        self.i += 1;
    }
    fn skip_ws(&mut self) {
        while matches!(self.peek(), Some(b' ' | b'\n' | b'\r' | b'\t')) {
            self.bump();
        }
    }
    fn parse_value(&mut self) -> Result<Value, String> {
        self.skip_ws();
        match self.peek() {
            Some(b'n') => self.consume_lit(b"null").map(|_| Value::Null),
            Some(b't') => self.consume_lit(b"true").map(|_| Value::Bool(true)),
            Some(b'f') => self.consume_lit(b"false").map(|_| Value::Bool(false)),
            Some(b'"') => self.parse_string().map(Value::String),
            Some(b'{') => self.parse_object(),
            Some(b'-') | Some(b'0'..=b'9') => self.parse_number(),
            other => Err(format!("unexpected {:?}", other.map(|c| c as char))),
        }
    }
    fn consume_lit(&mut self, lit: &[u8]) -> Result<(), String> {
        for &c in lit {
            if self.peek() != Some(c) {
                return Err("literal".into());
            }
            self.bump();
        }
        Ok(())
    }
    fn parse_string(&mut self) -> Result<String, String> {
        self.bump();
        let mut out = String::new();
        loop {
            match self.peek() {
                None => return Err("unterminated string".into()),
                Some(b'"') => {
                    self.bump();
                    return Ok(out);
                }
                Some(b'\\') => {
                    self.bump();
                    match self.peek() {
                        Some(b'"') => out.push('"'),
                        Some(b'\\') => out.push('\\'),
                        Some(b'n') => out.push('\n'),
                        Some(b't') => out.push('\t'),
                        Some(b'r') => out.push('\r'),
                        Some(b'/') => out.push('/'),
                        Some(c) => out.push(c as char),
                        None => return Err("escape".into()),
                    }
                    self.bump();
                }
                Some(c) => {
                    out.push(c as char);
                    self.bump();
                }
            }
        }
    }
    fn parse_number(&mut self) -> Result<Value, String> {
        let start = self.i;
        if self.peek() == Some(b'-') {
            self.bump();
        }
        while matches!(self.peek(), Some(b'0'..=b'9')) {
            self.bump();
        }
        if self.peek() == Some(b'.') {
            self.bump();
            while matches!(self.peek(), Some(b'0'..=b'9')) {
                self.bump();
            }
        }
        if matches!(self.peek(), Some(b'e' | b'E')) {
            self.bump();
            if matches!(self.peek(), Some(b'+' | b'-')) {
                self.bump();
            }
            while matches!(self.peek(), Some(b'0'..=b'9')) {
                self.bump();
            }
        }
        let s = std::str::from_utf8(&self.s[start..self.i]).map_err(|_| "utf8")?;
        s.parse::<f64>().map(Value::Number).map_err(|_| "number".into())
    }
    fn parse_object(&mut self) -> Result<Value, String> {
        self.bump();
        let mut map = BTreeMap::new();
        self.skip_ws();
        if self.peek() == Some(b'}') {
            self.bump();
            return Ok(Value::Object(map));
        }
        loop {
            self.skip_ws();
            if self.peek() != Some(b'"') {
                return Err("object key".into());
            }
            let key = self.parse_string()?;
            self.skip_ws();
            if self.peek() != Some(b':') {
                return Err("colon".into());
            }
            self.bump();
            let val = self.parse_value()?;
            map.insert(key, val);
            self.skip_ws();
            match self.peek() {
                Some(b',') => {
                    self.bump();
                    continue;
                }
                Some(b'}') => {
                    self.bump();
                    return Ok(Value::Object(map));
                }
                _ => return Err("object end".into()),
            }
        }
    }
}

pub fn dumps_compact_sorted(obj: &BTreeMap<String, Value>) -> String {
    let mut parts = Vec::new();
    for (k, v) in obj {
        parts.push(format!("\"{}\":{}", escape(k), dumps_val(v)));
    }
    format!("{{{}}}", parts.join(","))
}

fn dumps_val(v: &Value) -> String {
    match v {
        Value::Null => "null".into(),
        Value::Bool(true) => "true".into(),
        Value::Bool(false) => "false".into(),
        Value::Number(n) => {
            if n.fract() == 0.0 && n.abs() < 1e15 {
                format!("{}", *n as i64)
            } else {
                format!("{}", n)
            }
        }
        Value::String(s) => format!("\"{}\"", escape(s)),
        Value::Object(o) => dumps_compact_sorted(o),
    }
}

fn escape(s: &str) -> String {
    s.replace('\\', "\\\\").replace('"', "\\\"")
}
