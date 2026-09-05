# aion-enforcer (Rust) — pure std

Gate + Issuer AION **sans dépendances crates** (build offline).

## Build

```bash
cd enforcer_rs
cargo build --release
# si noexec: cp target/release/aion-* /tmp && chmod +x /tmp/aion-*
```

## Binaires

| Binaire | Rôle |
|---------|------|
| `aion-issuer` | Signe τ → Authorization (pas d'effet monde) |
| `aion-enforcer` | Vérifie jeton + mute `AION_WORLD_DIR` |

Env: `AION_ENFORCER_SECRET` (obligatoire), `AION_POLICY_HASH`, `AION_NONCE_DB`, `AION_WORLD_DIR`

Interop: `export AION_RUST_GATE=/tmp/aion-enforcer`

Python issuer → Rust gate validé. Rust issuer → Rust gate validé.
