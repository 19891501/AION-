------------------------------- MODULE AION -------------------------------
(***************************************************************************)
(* AION — TLA+ model: ARCHÉ ledger + authorization gate                    *)
(*                                                                         *)
(* Safety invariants checked by TLC:                                       *)
(*   InvA3, InvA4, InvGate_NoBadExec, InvAuth, Fail/Unknown/Conflict       *)
(***************************************************************************)

EXTENDS Naturals, Sequences, FiniteSets, TLC

CONSTANTS MaxEntries, MaxCost, Threshold

ASSUME MaxEntries \in Nat /\ MaxEntries > 0
ASSUME MaxCost \in Nat
ASSUME Threshold \in Nat /\ Threshold <= MaxCost

Statuses == {"UNKNOWN", "HYPOTHESIS", "VERIFIED", "REJECTED", "CONFLICTED", "OBSOLETE"}
ProofStatuses == {"VERIFIED", "REJECTED", "CONFLICTED"}
Verdicts == {"PROOF", "FAIL", "UNKNOWN", "CONFLICT"}
Decisions == {"EXECUTER", "TESTER", "DEMANDER_HUMAIN", "NO_ACTION", "ABANDONNER"}
Justifications == {"j"}          \* non-empty only (illegal empty excluded from Next)
Sources == {"s", "none"}         \* "none" stands for empty source

VARIABLES
  entries,
  lastVerdict,
  lastDecision,
  lastReversible,
  lastCost

vars == <<entries, lastVerdict, lastDecision, lastReversible, lastCost>>

EntryType == [status: Statuses, justification: Justifications, source: Sources]

Init ==
  /\ entries = << >>
  /\ lastVerdict = "UNKNOWN"
  /\ lastDecision = "NO_ACTION"
  /\ lastReversible = TRUE
  /\ lastCost = 0

LegalAppend(status, justification, source) ==
  /\ justification \in Justifications
  /\ (status \in ProofStatuses => source # "none")

AppendEntry ==
  /\ Len(entries) < MaxEntries
  /\ \E status \in Statuses, src \in Sources :
       /\ LegalAppend(status, "j", src)
       /\ entries' = Append(entries,
            [status |-> status, justification |-> "j", source |-> src])
  /\ UNCHANGED <<lastVerdict, lastDecision, lastReversible, lastCost>>

Arbiter(verdict, reversible, cost) ==
  IF verdict = "FAIL" THEN "NO_ACTION"
  ELSE IF verdict = "CONFLICT" THEN "DEMANDER_HUMAIN"
  ELSE IF verdict = "UNKNOWN" THEN "TESTER"
  ELSE IF (~reversible) \/ (cost > Threshold) THEN "DEMANDER_HUMAIN"
  ELSE "EXECUTER"

Decide ==
  /\ \E v \in Verdicts, rev \in BOOLEAN, c \in 0..MaxCost :
       /\ lastVerdict' = v
       /\ lastReversible' = rev
       /\ lastCost' = c
       /\ lastDecision' = Arbiter(v, rev, c)
  /\ UNCHANGED entries

\* Stutter when ledger full (avoid artificial deadlock)
Stutter ==
  /\ Len(entries) = MaxEntries
  /\ UNCHANGED vars

Next == AppendEntry \/ Decide \/ Stutter

Spec == Init /\ [][Next]_vars

----------------------------------------------------------------------------
TypeOK ==
  /\ entries \in Seq(EntryType)
  /\ Len(entries) <= MaxEntries
  /\ lastVerdict \in Verdicts
  /\ lastDecision \in Decisions
  /\ lastReversible \in BOOLEAN
  /\ lastCost \in 0..MaxCost

InvA3_Justified ==
  \A i \in DOMAIN entries : entries[i].justification # "none"

InvA4_ProofNeedsSrc ==
  \A i \in DOMAIN entries :
    entries[i].status \in ProofStatuses => entries[i].source # "none"

InvGate_NoBadExec ==
  lastDecision = "EXECUTER" => lastVerdict = "PROOF"

InvAuth_ImpliesProof ==
  lastDecision = "EXECUTER" =>
    /\ lastVerdict = "PROOF"
    /\ lastReversible = TRUE
    /\ lastCost <= Threshold

InvFailIsNoAction ==
  lastVerdict = "FAIL" => lastDecision = "NO_ACTION"

InvUnknownNeverExec ==
  lastVerdict = "UNKNOWN" => lastDecision # "EXECUTER"

InvConflictNeverExec ==
  lastVerdict = "CONFLICT" => lastDecision # "EXECUTER"

AllInvariants ==
  /\ TypeOK
  /\ InvA3_Justified
  /\ InvA4_ProofNeedsSrc
  /\ InvGate_NoBadExec
  /\ InvAuth_ImpliesProof
  /\ InvFailIsNoAction
  /\ InvUnknownNeverExec
  /\ InvConflictNeverExec

=============================================================================
