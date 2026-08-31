# Why Hindsight Open-Closed is worth measuring

Rationale behind step 3(c) of `tdd-cycle`. Read when the count says to lift and the
lift looks like overkill, or when deciding whether to accept a lockstep edit.

Modifying many existing files burns scarce context on two fronts: humans can only hold so much in their head before the structure calcifies, and AI agents have bounded context windows plus per-token costs that scale with files-read-and-edited per change. OCP isn't aesthetic — it's a hard cost lever on both human cognitive load and agent token spend, and a codebase that violates OCP gets disproportionately more expensive to evolve as it grows.
