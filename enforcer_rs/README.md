# aion-enforcer (Rust)

Gate process. Même JSON que `python -m aion.gate`.

```bash
cargo build --release
AION_ENFORCER_SECRET=dev-secret ./target/release/aion-enforcer
```

Voir `src/main.rs`. Si crates.io down, utiliser le gate Python.
