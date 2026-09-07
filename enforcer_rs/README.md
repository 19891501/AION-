# aion-enforcer (Rust) — pure std

Gate + Issuer AION **sans dépendances crates** (build offline).

## Build

```bash
cd enforcer_rs
cargo build --release
# si noexec sur target/: cp target/release/aion-* /tmp && chmod +x /tmp/aion-*
```

## Binaires

| Binaire | Rôle |
|---------|------|
| `aion-issuer` | Signe τ → Authorization (pas d'effet monde) |
| `aion-enforcer` | Vérifie jeton + mute `AION_WORLD_DIR` |

## Env

- `AION_ENFORCER_SECRET` (obligatoire)
- `AION_POLICY_HASH` (défaut `policy-v0`)
- `AION_NONCE_DB`
- `AION_WORLD_DIR`

## Interop Python

```bash
export AION_RUST_GATE=/tmp/aion-enforcer
# gate_bridge / ControlPlane utilisent le binaire si exécutable
```

## Macaroons

Délégation atténuable (HMAC chaîné, zero crates) :

| Binaire | Rôle |
|---------|------|
| `aion-macaroon` | `mint` / `caveat` / `verify` |

```bash
export AION_MACAROON_KEY=dev
M=$(./aion-macaroon mint human-policy aion-gate)
echo "$M" | ./aion-macaroon caveat "amount <= 100" | ./aion-macaroon caveat "amount <= 40" > /tmp/m.json
./aion-macaroon verify '{"macaroon":'"$(cat /tmp/m.json)"',"context":{"action":"transfer","amount":20,"target":"iban-X"}}'
```

Propriété : on peut restreindre hors ligne ; élargir ou retirer un caveat casse la signature.
`vid` third-party est en clair (lab). Production : chiffrer vers le tiers.

```bash
CARGO_TARGET_DIR=/tmp/aion-rs cargo test -p aion-enforcer --lib
```

## Tests manuels

```bash
export AION_ENFORCER_SECRET=dev AION_WORLD_DIR=/tmp/w AION_NONCE_DB=/tmp/n
AUTH=$(./aion-issuer '{"transition":{"actor":"a","action":"b","target":"c","params":{}},"ttl_sec":60}')
echo "$AUTH" | jq .
# coller auth dans payload gate…
```
