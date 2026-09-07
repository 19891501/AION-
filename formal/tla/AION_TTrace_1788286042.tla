---- MODULE AION_TTrace_1788286042 ----
EXTENDS Sequences, TLCExt, Toolbox, AION, Naturals, TLC

_expression ==
    LET AION_TEExpression == INSTANCE AION_TEExpression
    IN AION_TEExpression!expression
----

_trace ==
    LET AION_TETrace == INSTANCE AION_TETrace
    IN AION_TETrace!trace
----

_inv ==
    ~(
        TLCGet("level") = Len(_TETrace)
        /\
        entries = (<<[status |-> "UNKNOWN", justification |-> "j", source |-> "s"], [status |-> "UNKNOWN", justification |-> "j", source |-> "s"], [status |-> "UNKNOWN", justification |-> "j", source |-> "s"]>>)
        /\
        lastReversible = (FALSE)
        /\
        lastCost = (0)
        /\
        step = (6)
        /\
        lastDecision = ("TESTER")
        /\
        lastVerdict = ("UNKNOWN")
    )
----

_init ==
    /\ entries = _TETrace[1].entries
    /\ lastDecision = _TETrace[1].lastDecision
    /\ lastReversible = _TETrace[1].lastReversible
    /\ lastVerdict = _TETrace[1].lastVerdict
    /\ step = _TETrace[1].step
    /\ lastCost = _TETrace[1].lastCost
----

_next ==
    /\ \E i,j \in DOMAIN _TETrace:
        /\ \/ /\ j = i + 1
              /\ i = TLCGet("level")
        /\ entries  = _TETrace[i].entries
        /\ entries' = _TETrace[j].entries
        /\ lastDecision  = _TETrace[i].lastDecision
        /\ lastDecision' = _TETrace[j].lastDecision
        /\ lastReversible  = _TETrace[i].lastReversible
        /\ lastReversible' = _TETrace[j].lastReversible
        /\ lastVerdict  = _TETrace[i].lastVerdict
        /\ lastVerdict' = _TETrace[j].lastVerdict
        /\ step  = _TETrace[i].step
        /\ step' = _TETrace[j].step
        /\ lastCost  = _TETrace[i].lastCost
        /\ lastCost' = _TETrace[j].lastCost

\* Uncomment the ASSUME below to write the states of the error trace
\* to the given file in Json format. Note that you can pass any tuple
\* to `JsonSerialize`. For example, a sub-sequence of _TETrace.
    \* ASSUME
    \*     LET J == INSTANCE Json
    \*         IN J!JsonSerialize("AION_TTrace_1788286042.json", _TETrace)

=============================================================================

 Note that you can extract this module `AION_TEExpression`
  to a dedicated file to reuse `expression` (the module in the 
  dedicated `AION_TEExpression.tla` file takes precedence 
  over the module `AION_TEExpression` below).

---- MODULE AION_TEExpression ----
EXTENDS Sequences, TLCExt, Toolbox, AION, Naturals, TLC

expression == 
    [
        \* To hide variables of the `AION` spec from the error trace,
        \* remove the variables below.  The trace will be written in the order
        \* of the fields of this record.
        entries |-> entries
        ,lastDecision |-> lastDecision
        ,lastReversible |-> lastReversible
        ,lastVerdict |-> lastVerdict
        ,step |-> step
        ,lastCost |-> lastCost
        
        \* Put additional constant-, state-, and action-level expressions here:
        \* ,_stateNumber |-> _TEPosition
        \* ,_entriesUnchanged |-> entries = entries'
        
        \* Format the `entries` variable as Json value.
        \* ,_entriesJson |->
        \*     LET J == INSTANCE Json
        \*     IN J!ToJson(entries)
        
        \* Lastly, you may build expressions over arbitrary sets of states by
        \* leveraging the _TETrace operator.  For example, this is how to
        \* count the number of times a spec variable changed up to the current
        \* state in the trace.
        \* ,_entriesModCount |->
        \*     LET F[s \in DOMAIN _TETrace] ==
        \*         IF s = 1 THEN 0
        \*         ELSE IF _TETrace[s].entries # _TETrace[s-1].entries
        \*             THEN 1 + F[s-1] ELSE F[s-1]
        \*     IN F[_TEPosition - 1]
    ]

=============================================================================



Parsing and semantic processing can take forever if the trace below is long.
 In this case, it is advised to uncomment the module below to deserialize the
 trace from a generated binary file.

\*
\*---- MODULE AION_TETrace ----
\*EXTENDS IOUtils, AION, TLC
\*
\*trace == IODeserialize("AION_TTrace_1788286042.bin", TRUE)
\*
\*=============================================================================
\*

---- MODULE AION_TETrace ----
EXTENDS AION, TLC

trace == 
    <<
    ([entries |-> <<>>,lastReversible |-> TRUE,lastCost |-> 0,step |-> 0,lastDecision |-> "NO_ACTION",lastVerdict |-> "UNKNOWN"]),
    ([entries |-> <<[status |-> "UNKNOWN", justification |-> "j", source |-> "s"]>>,lastReversible |-> TRUE,lastCost |-> 0,step |-> 1,lastDecision |-> "NO_ACTION",lastVerdict |-> "UNKNOWN"]),
    ([entries |-> <<[status |-> "UNKNOWN", justification |-> "j", source |-> "s"], [status |-> "UNKNOWN", justification |-> "j", source |-> "s"]>>,lastReversible |-> TRUE,lastCost |-> 0,step |-> 2,lastDecision |-> "NO_ACTION",lastVerdict |-> "UNKNOWN"]),
    ([entries |-> <<[status |-> "UNKNOWN", justification |-> "j", source |-> "s"], [status |-> "UNKNOWN", justification |-> "j", source |-> "s"], [status |-> "UNKNOWN", justification |-> "j", source |-> "s"]>>,lastReversible |-> TRUE,lastCost |-> 0,step |-> 3,lastDecision |-> "NO_ACTION",lastVerdict |-> "UNKNOWN"]),
    ([entries |-> <<[status |-> "UNKNOWN", justification |-> "j", source |-> "s"], [status |-> "UNKNOWN", justification |-> "j", source |-> "s"], [status |-> "UNKNOWN", justification |-> "j", source |-> "s"]>>,lastReversible |-> FALSE,lastCost |-> 0,step |-> 4,lastDecision |-> "TESTER",lastVerdict |-> "UNKNOWN"]),
    ([entries |-> <<[status |-> "UNKNOWN", justification |-> "j", source |-> "s"], [status |-> "UNKNOWN", justification |-> "j", source |-> "s"], [status |-> "UNKNOWN", justification |-> "j", source |-> "s"]>>,lastReversible |-> FALSE,lastCost |-> 0,step |-> 5,lastDecision |-> "TESTER",lastVerdict |-> "UNKNOWN"]),
    ([entries |-> <<[status |-> "UNKNOWN", justification |-> "j", source |-> "s"], [status |-> "UNKNOWN", justification |-> "j", source |-> "s"], [status |-> "UNKNOWN", justification |-> "j", source |-> "s"]>>,lastReversible |-> FALSE,lastCost |-> 0,step |-> 6,lastDecision |-> "TESTER",lastVerdict |-> "UNKNOWN"])
    >>
----


=============================================================================

---- CONFIG AION_TTrace_1788286042 ----
CONSTANTS
    MaxEntries = 3
    MaxCost = 2
    Threshold = 1

INVARIANT
    _inv

CHECK_DEADLOCK
    \* CHECK_DEADLOCK off because of PROPERTY or INVARIANT above.
    FALSE

INIT
    _init

NEXT
    _next

CONSTANT
    _TETrace <- _trace

ALIAS
    _expression
=============================================================================
\* Generated on Tue Sep 01 18:07:32 UTC 2026