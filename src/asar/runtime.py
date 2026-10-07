from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .adaptation import GuardedPlannerAdapter
from .authority import AuthorityPolicy, IndependentActionAuthority
from .contracts import CycleResult, ModalityEstimate, QualityReport, StateEstimate
from .evidence import EvidenceLedger
from .fusion import ReliabilityWeightedFusion
from .interfaces import AdaptivePlanner, DomainAdapter
from .quality import SignalPolicy, SignalQualityEvaluator


class SenseActRuntime:
    """Domain-neutral closed-loop orchestration.

    Domain-specific sensing, feature extraction, planning, and actuation arrive through
    injected contracts. The runtime owns quality gating, fusion, independent authority,
    post-action observation, bounded adaptation, and evidence sequencing.
    """

    def __init__(
        self,
        *,
        adapter: DomainAdapter,
        quality_policies: Mapping[str, SignalPolicy],
        authority_policy: AuthorityPolicy,
        planner: AdaptivePlanner,
        evidence_path: Path | None = None,
    ) -> None:
        self.adapter = adapter
        self.quality_policies = dict(quality_policies)
        self.authority_policy = authority_policy
        self.quality = SignalQualityEvaluator()
        self.fusion = ReliabilityWeightedFusion()
        self.planner = planner
        self.authority = IndependentActionAuthority()
        self.adaptation = GuardedPlannerAdapter()
        self.ledger = EvidenceLedger(evidence_path)
        self.cycle_index = 0

    def _observe(self) -> tuple[StateEstimate, dict[str, QualityReport]]:
        frames = self.adapter.observe()
        quality: dict[str, QualityReport] = {}
        estimates: list[ModalityEstimate] = []
        for frame in frames:
            policy = self.quality_policies.get(frame.modality)
            if policy is None:
                quality[frame.modality] = QualityReport(
                    frame.modality,
                    False,
                    0.0,
                    ("missing_quality_policy",),
                )
                continue
            report = self.quality.evaluate(frame, policy)
            quality[frame.modality] = report
            if report.valid:
                estimates.append(self.adapter.estimate(frame, quality=report.score))
        state = self.fusion.fuse(estimates)
        return state, quality

    def cycle(self) -> CycleResult:
        cycle = self.cycle_index
        self.cycle_index += 1
        before, quality = self._observe()
        request = self.planner.propose(before, cycle=cycle)
        authority = self.authority.decide(request, before, quality, self.authority_policy)
        execution = self.adapter.execute(request=request, decision=authority)
        after, after_quality = self._observe()
        before_error = self.planner.error(before)
        after_error = self.planner.error(after)
        adaptation = self.adaptation.update(
            current_gain=self.planner.gain,
            before_error=before_error,
            after_error=after_error,
            disposition=authority.disposition,
        )
        if adaptation.changed:
            self.planner.gain = adaptation.new_gain
        goal_reached = self.planner.goal_reached(after)
        payload = {
            "cycle": cycle,
            "before": before,
            "quality": quality,
            "request": request,
            "authority": authority,
            "execution": execution,
            "after": after,
            "after_quality": after_quality,
            "adaptation": adaptation,
            "goal_reached": goal_reached,
        }
        evidence_digest = self.ledger.append("closed_loop_cycle", payload)
        return CycleResult(
            cycle,
            before,
            request,
            authority,
            execution,
            after,
            adaptation,
            goal_reached,
            evidence_digest,
        )
