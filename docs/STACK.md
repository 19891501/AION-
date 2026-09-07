# Stack AION — décision technique

## Maintenant (lab)

| Couche | Techno |
|--------|--------|
| Kernel / Veritas / Arbitre / banc | **Python** |
| Enforcer in-process | Python (`enforcer.py`) |
| **Gate process isolé** | Python `-m aion.gate` via `gate_bridge` |
| Attack bench | Python 0 € |

Principe : le process qui *agit* n’est pas obligé d’être le process agent.  
La bridge est le seul appelant supporté du monde lab.

## Rust (prêt, build bloqué crates.io 502 ici)

`enforcer_rs/` — même contrat JSON que `aion.gate`.  
Quand le registry est dispo :

```bash
cd enforcer_rs && cargo build --release
AION_ENFORCER_SECRET=... ./target/release/aion-enforcer
# ou invoke_gate(..., rust_bin=...)
```

## Ce qu’on ne fait pas

- Réécrire le kernel en Rust
- Boîtier avant gate process vert en CI
