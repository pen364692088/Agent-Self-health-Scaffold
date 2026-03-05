#!/usr/bin/env python3
"""Script to add MVP-7.6 methods to SelfModelV0 class."""

import sys
import re

# Methods to add to SelfModelV0 class
methods_code = '''
    # ========================= MVP-7.6 Phase 1: Self-Conflict & Manifest/Replay =========================
    
    def compute_self_conflict(
        self,
        event_type: str,
        meta: Optional[Dict[str, Any]] = None,
        relationship_state: Optional[Dict[str, float]] = None,
    ) -> float:
        """
        Calculate self_conflict based on three types of prediction errors.
        
        Three components (weighted average):
        1. Value conflict (0.4 weight): Event conflicts with core values
        2. Capability failure (0.3 weight): Event indicates capability failure
        3. Identity threat (0.3 weight): Event threatens identity stability
        
        Args:
            event_type: Type of event (e.g., "user_message", "feedback", "world_event")
            meta: Event metadata (may contain value_alignment, success, identity_relevance)
            relationship_state: Current relationship state (bond, trust, grudge)
        
        Returns:
            float: Self-conflict score in range [0, 1], where 1 = maximum conflict
        """
        meta = meta or {}
        relationship_state = relationship_state or {}
        
        # Component 1: Value conflict (0-1)
        value_conflict = self._compute_value_conflict(event_type, meta)
        
        # Component 2: Capability failure (0-1)
        capability_conflict = self._compute_capability_conflict(event_type, meta)
        
        # Component 3: Identity threat (0-1)
        identity_conflict = self._compute_identity_conflict(event_type, meta, relationship_state)
        
        # Weighted average (weights sum to 1.0)
        weights = {"value": 0.4, "capability": 0.3, "identity": 0.3}
        self_conflict = (
            weights["value"] * value_conflict +
            weights["capability"] * capability_conflict +
            weights["identity"] * identity_conflict
        )
        
        return max(0.0, min(1.0, self_conflict))
    
    def _compute_value_conflict(self, event_type: str, meta: Dict[str, Any]) -> float:
        """Compute value conflict component (0-1)."""
        # Check if meta provides explicit value alignment
        value_alignment = meta.get("value_alignment", None)
        if value_alignment is not None:
            return 1.0 - value_alignment
        
        # Infer from event type
        event_lower = event_type.lower()
        
        if any(kw in event_lower for kw in ["deception", "betrayal", "harm", "threat", "rejection"]):
            return 0.9
        
        if any(kw in event_lower for kw in ["conflict", "disagreement", "failure", "mistake"]):
            return 0.6
        
        if any(kw in event_lower for kw in ["neutral", "routine", "information"]):
            return 0.2
        
        return 0.3
    
    def _compute_capability_conflict(self, event_type: str, meta: Dict[str, Any]) -> float:
        """Compute capability failure component (0-1)."""
        success = meta.get("success", None)
        if success is not None:
            capability_name = meta.get("capability", None)
            if capability_name:
                belief = self._get_capability_belief(capability_name)
                if belief:
                    expected = belief["capability"] * belief["confidence"]
                    actual = 1.0 if success else 0.0
                    return abs(expected - actual)
            return 0.0 if success else 0.7
        
        event_lower = event_type.lower()
        
        if any(kw in event_lower for kw in ["failure", "error", "unable", "cannot"]):
            return 0.8
        
        if any(kw in event_lower for kw in ["success", "achieved", "completed"]):
            return 0.1
        
        return 0.3
    
    def _compute_identity_conflict(
        self, event_type: str, meta: Dict[str, Any], relationship_state: Dict[str, float]
    ) -> float:
        """Compute identity threat component (0-1)."""
        identity_threat = meta.get("identity_threat", 0.0)
        if identity_threat > 0:
            return min(1.0, identity_threat)
        
        bond = relationship_state.get("bond", 0.5)
        trust = relationship_state.get("trust", 0.5)
        
        connection_value = self.identity.value_weights.get("connection", 0.7)
        if connection_value > 0.6 and (bond < 0.3 or trust < 0.3):
            return 0.7
        
        event_lower = event_type.lower()
        
        if any(kw in event_lower for kw in ["rejection", "betrayal", "abandonment", "exclusion"]):
            return 0.9
        
        if any(kw in event_lower for kw in ["criticism", "blame", "accusation"]):
            return 0.6
        
        return 0.2
    
    def _get_capability_belief(self, name: str) -> Optional[Dict[str, float]]:
        """Get capability belief by name (simplified for SelfModelV0)."""
        return None
    
    def apply_event(
        self,
        event: Dict[str, Any],
        ctx: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update self_model state based on an event and return conflict information.
        
        Args:
            event: Event dict with keys: type, meta, timestamp
            ctx: Context dict with relationship_state and other fields
        
        Returns:
            Dict with: delta, self_conflict, evidence, old_state, new_state
        """
        ctx = ctx or {}
        event_type = event.get("type", "unknown")
        meta = event.get("meta", {})
        relationship_state = ctx.get("relationship_state", {})
        
        # Calculate self_conflict
        self_conflict = self.compute_self_conflict(event_type, meta, relationship_state)
        
        # Track state before update
        old_state = self.snapshot()
        
        # Apply updates
        delta = self._apply_event_updates(event, ctx, self_conflict)
        
        # Update timestamp
        self.updated_at = time.time()
        
        # Build evidence
        evidence = {
            "event_type": event_type,
            "event_meta": meta,
            "relationship_state": relationship_state,
            "conflict_components": {
                "value_conflict": self._compute_value_conflict(event_type, meta),
                "capability_conflict": self._compute_capability_conflict(event_type, meta),
                "identity_conflict": self._compute_identity_conflict(event_type, meta, relationship_state),
            },
        }
        
        return {
            "delta": delta,
            "self_conflict": self_conflict,
            "evidence": evidence,
            "old_state": old_state,
            "new_state": self.snapshot(),
        }
    
    def _apply_event_updates(
        self,
        event: Dict[str, Any],
        ctx: Dict[str, Any],
        self_conflict: float,
    ) -> Dict[str, Any]:
        """Apply state updates based on event."""
        delta = {}
        meta = event.get("meta", {})
        event_type = event.get("type", "unknown")
        
        # Update cognitive state based on conflict
        if self_conflict > 0.5:
            old_uncertainty = self.cognitive.uncertainty
            self.cognitive.uncertainty = min(1.0, self.cognitive.uncertainty + 0.1)
            if self.cognitive.uncertainty != old_uncertainty:
                delta["cognitive.uncertainty"] = {
                    "old": old_uncertainty,
                    "new": self.cognitive.uncertainty,
                }
        
        # Update based on feedback events
        if "feedback" in event_type.lower():
            success = meta.get("success", None)
            if success is True:
                old_confidence = self.cognitive.confidence
                self.cognitive.confidence = min(1.0, self.cognitive.confidence + 0.05)
                delta["cognitive.confidence"] = {
                    "old": old_confidence,
                    "new": self.cognitive.confidence,
                }
            elif success is False:
                old_confidence = self.cognitive.confidence
                self.cognitive.confidence = max(0.0, self.cognitive.confidence - 0.05)
                delta["cognitive.confidence"] = {
                    "old": old_confidence,
                    "new": self.cognitive.confidence,
                }
        
        # Update relational state
        if "relationship" in meta:
            rel_meta = meta["relationship"]
            if "bond_delta" in rel_meta:
                old_bond = self.relational.bond
                self.relational.bond = max(0.0, min(1.0, self.relational.bond + rel_meta["bond_delta"]))
                delta["relational.bond"] = {
                    "old": old_bond,
                    "new": self.relational.bond,
                }
        
        return delta
    
    def compute_hash(self) -> str:
        """
        Compute deterministic hash of self_model state for manifest/replay.
        
        Returns:
            str: Hex-encoded SHA-256 hash (64 characters)
        """
        import hashlib
        import json
        
        state_dict = {
            "bodily": {
                "energy": self.bodily.energy,
                "social_safety": self.bodily.social_safety,
                "focus_fatigue": self.bodily.focus_fatigue,
            },
            "relational": {
                "focus_target": self.relational.focus_target,
                "bond": self.relational.bond,
                "grudge": self.relational.grudge,
                "trust": self.relational.trust,
                "repair_bank": self.relational.repair_bank,
                "ledger_summary": json.dumps(self.relational.ledger_summary, sort_keys=True),
            },
            "cognitive": {
                "confidence": self.cognitive.confidence,
                "uncertainty": self.cognitive.uncertainty,
                "regulation_budget": self.cognitive.regulation_budget,
            },
            "identity": {
                "traits": sorted(self.identity.traits),
                "value_weights": json.dumps(self.identity.value_weights, sort_keys=True),
            },
        }
        
        canonical = json.dumps(state_dict, sort_keys=True, separators=(",", ":"))
        hash_bytes = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        
        return hash_bytes
    
    def snapshot(self) -> Dict[str, Any]:
        """
        Return serializable state snapshot for persistence/replay.
        
        Returns:
            Dict: Complete serializable state
        """
        return {
            "bodily": {
                "energy": self.bodily.energy,
                "social_safety": self.bodily.social_safety,
                "focus_fatigue": self.bodily.focus_fatigue,
            },
            "relational": {
                "focus_target": self.relational.focus_target,
                "bond": self.relational.bond,
                "grudge": self.relational.grudge,
                "trust": self.relational.trust,
                "repair_bank": self.relational.repair_bank,
                "ledger_summary": dict(self.relational.ledger_summary),
            },
            "cognitive": {
                "confidence": self.cognitive.confidence,
                "uncertainty": self.cognitive.uncertainty,
                "regulation_budget": self.cognitive.regulation_budget,
            },
            "identity": {
                "traits": list(self.identity.traits),
                "value_weights": dict(self.identity.value_weights),
            },
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_snapshot(cls, snapshot: Dict[str, Any]) -> "SelfModelV0":
        """
        Reconstruct SelfModelV0 from snapshot.
        
        Args:
            snapshot: Dict from snapshot() method
        
        Returns:
            SelfModelV0: Reconstructed instance
        """
        bodily = BodilySnapshot(**snapshot.get("bodily", {}))
        relational = RelationalSnapshot(**snapshot.get("relational", {}))
        cognitive = CognitiveSnapshot(**snapshot.get("cognitive", {}))
        identity = IdentitySnapshot(**snapshot.get("identity", {}))
        
        return cls(
            bodily=bodily,
            relational=relational,
            cognitive=cognitive,
            identity=identity,
            updated_at=snapshot.get("updated_at", time.time()),
        )

'''

# Read the original file
with open('/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/self_model.py', 'r') as f:
    content = f.read()

# Pattern to match the end of SelfModelV0 class definition
pattern = r'(class SelfModelV0\(BaseModel\):.*?updated_at: float = Field\(default_factory=time\.time\))\n(\def build_self_model_v0)'

match = re.search(pattern, content, re.DOTALL)

if match:
    # Insert methods between class definition and build_self_model_v0 function
    before = content[:match.end(1)]
    after = content[match.end(1):]
    
    new_content = before + methods_code + '\n' + after
    
    with open('/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/self_model.py', 'w') as f:
        f.write(new_content)
    
    print("Successfully added methods to SelfModelV0 class")
else:
    print("ERROR: Could not find insertion point in file")
    sys.exit(1)
