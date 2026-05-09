from __future__ import annotations

import argparse
import json
import sys
import uuid

from project.common.models import HypothesisOutput, utc_now_iso
from project.data.db import DuckDBAccess
from project.data.models import HypothesisEvaluation
from project.data.repository import DataRepository
from project.hypotheses.engine import evaluate_hypotheses
from project.hypotheses.registry import HypothesisRegistry
from project.signals.pipeline import compute_latest_price_signals
from project.signals.registry import default_signal_registry
from project.trade_engine.generator import generate_trade_ideas
from project.validation.engine import ValidationEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="project")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("init-db")
    run_parser = subcommands.add_parser("run-batch")
    run_parser.add_argument("asset_id")
    run_parser.add_argument("--database", default="project_mft.duckdb")
    review_parser = subcommands.add_parser("review-trade-idea")
    review_parser.add_argument("trade_id")
    review_parser.add_argument(
        "action",
        choices=["approve", "reject", "watchlist"],
        help="Decision action to take",
    )
    review_parser.add_argument(
        "--reason",
        choices=["low_confidence", "conflicting_signals", "risk_constraints", "intuition_override", "market_conditions", "duplicate_exposure"],
        help="Structured reason for the decision",
    )
    review_parser.add_argument(
        "--notes",
        default="",
        help="Optional notes for the decision",
    )
    review_parser.add_argument(
        "--database",
        default="project_mft.duckdb",
        help="Database file path",
    )
    
    # Track 4 - Research Operations Team: Observability CLI commands
    show_trade_idea_parser = subcommands.add_parser("show-trade-idea")
    show_trade_idea_parser.add_argument("trade_id")
    show_trade_idea_parser.add_argument(
        "--database",
        default="project_mft.duckdb",
        help="Database file path",
    )
    
    summarize_batch_parser = subcommands.add_parser("summarize-batch")
    summarize_batch_parser.add_argument("asset_id")
    summarize_batch_parser.add_argument(
        "--database",
        default="project_mft.duckdb",
        help="Database file path",
    )
    
    show_hy_eval_parser = subcommands.add_parser("show-hypothesis-evaluations")
    show_hy_eval_parser.add_argument(
        "--asset-id",
        help="Filter by asset ID (optional)",
    )
    show_hy_eval_parser.add_argument(
        "--hypothesis-id",
        help="Filter by hypothesis ID (optional)",
    )
    show_hy_eval_parser.add_argument(
        "--database",
        default="project_mft.duckdb",
        help="Database file path",
    )
    
    show_val_failures_parser = subcommands.add_parser("show-validation-failures")
    show_val_failures_parser.add_argument(
        "--database",
        default="project_mft.duckdb",
        help="Database file path",
    )
    
    # New observability commands for enhanced research capabilities
    show_competition_parser = subcommands.add_parser("show-competition")
    show_competition_parser.add_argument(
        "--asset-id",
        help="Filter by asset ID (optional)",
    )
    show_competition_parser.add_argument(
        "--direction",
        choices=["long", "short", "flat"],
        help="Filter by direction (optional)",
    )
    show_competition_parser.add_argument(
        "--database",
        default="project_mft.duckdb",
        help="Database file path",
    )
    
    show_explanation_parser = subcommands.add_parser("show-explanation")
    show_explanation_parser.add_argument("evaluation_id")
    show_explanation_parser.add_argument(
        "--database",
        default="project_mft.duckdb",
        help="Database file path",
    )
    
    show_signal_lineage_parser = subcommands.add_parser("show-signal-lineage")
    show_signal_lineage_parser.add_argument("asset_id")
    show_signal_lineage_parser.add_argument(
        "--database",
        default="project_mft.duckdb",
        help="Database file path",
    )
    
    show_validation_path_parser = subcommands.add_parser("show-validation-path")
    show_validation_path_parser.add_argument("evaluation_id")
    show_validation_path_parser.add_argument(
        "--database",
        default="project_mft.duckdb",
        help="Database file path",
    )
    
    list_rejected_hypotheses_parser = subcommands.add_parser("list-rejected-hypotheses")
    list_rejected_hypotheses_parser.add_argument(
        "--database",
        default="project_mft.duckdb",
        help="Database file path",
    )
    
    report_hypotheses_parser = subcommands.add_parser("report-hypotheses")
    report_hypotheses_parser.add_argument(
        "--horizon",
        type=int,
        choices=[1, 5, 20],
        default=20,
        help="Evaluation horizon to report (1, 5, or 20)",
    )
    report_hypotheses_parser.add_argument(
        "--database",
        default="project_mft.duckdb",
        help="Database file path",
    )

    backtest_parser = subcommands.add_parser("backtest-hypothesis")
    backtest_parser.add_argument("hypothesis_id")
    backtest_parser.add_argument("asset_symbol")
    backtest_parser.add_argument("start_date", help="Start date (YYYY-MM-DD)")
    backtest_parser.add_argument("end_date", help="End date (YYYY-MM-DD)")
    backtest_parser.add_argument(
        "--database",
        default="project_mft.duckdb",
        help="Database file path",
    )
    
    return parser


def main(argv: list[str] | None = None) -> int:
    import sys
    print(f"DEBUG: argv = {argv}", file=sys.stderr); print("DEBUG: Entering main function", file=sys.stderr)
    import json
    import uuid
    from project.common.models import HypothesisOutput, utc_now_iso
    from project.data.models import HypothesisEvaluation
    from project.data.repository import DataRepository
    from project.hypotheses.engine import evaluate_hypotheses
    from project.hypotheses.registry import HypothesisRegistry
    from project.signals.pipeline import compute_latest_price_signals
    from project.signals.registry import default_signal_registry
    from project.trade_engine.generator import generate_trade_ideas
    from project.validation.engine import ValidationEngine
    args = build_parser().parse_args(argv); print(f"DEBUG: Parsed args: {args}", file=sys.stderr); print(f"DEBUG: args.command = {repr(args.command)}", file=sys.stderr); print(f"DEBUG: type(args.command) = {type(args.command)}", file=sys.stderr)
    print(f"DEBUG: args.command = {args.command}", file=sys.stderr)
    db = DuckDBAccess(getattr(args, "database", "project_mft.duckdb"))
    repository = DataRepository(db)
    repository.initialize()

    if args.command == "init-db":
        print(json.dumps({"status": "ok", "schema": "initialized"}))
        db.close()
        return 0

    if args.command == "run-batch":
        from project.hypotheses.rsi_mean_reversion import RSIMeanReversionHypothesis
        from project.hypotheses.ma_crossover import MACrossoverHypothesis
        # Look up the asset to get the correct asset_id (with prefix)
        assets = repository.list_assets()
        asset = next((a for a in assets if a.symbol == args.asset_id.upper()), None)
        if asset is None:
            print(json.dumps({"error": f"Asset {args.asset_id} not found"}))
            db.close()
            return 1
        signals = compute_latest_price_signals(repository, default_signal_registry(), asset.asset_id)
        outputs = evaluate_hypotheses(asset.asset_id, signals, (RSIMeanReversionHypothesis(), MACrossoverHypothesis()))
        
        # Persist all hypothesis evaluations
        hypothesis_evaluations = []
        for output in outputs:
            evaluation_id = f"eval:{output.asset_id}:{output.hypothesis_id}:{output.version}:{uuid.uuid4()}"
            evaluation = HypothesisEvaluation(
                evaluation_id=evaluation_id,
                asset_id=output.asset_id,
                hypothesis_id=output.hypothesis_id,
                hypothesis_version=output.version,
                timestamp=output.timestamp if hasattr(output, 'timestamp') else utc_now_iso(),
                direction=output.direction,
                confidence=output.confidence,
                signals_snapshot_json=json.dumps(dict(sorted(output.signals_snapshot.items())), sort_keys=True),
                explanation_json=json.dumps(output.explanation, sort_keys=True),
                generated_trade_idea=False,  # Will be updated if trade idea is generated
                validation_result_json=None,  # Will be updated after validation
                created_at=utc_now_iso(),
            )
            hypothesis_evaluations.append(evaluation)
            repository.persist_hypothesis_evaluation(evaluation)
        
        # Validate hypothesis evaluations
        validation_engine = ValidationEngine()
        hypothesis_registry = HypothesisRegistry()
        # Register the RSI mean reversion hypothesis for validation
        from project.hypotheses.rsi_mean_reversion import RSIMeanReversionHypothesis
        rsi_hypothesis = RSIMeanReversionHypothesis()
        hypothesis_registry.register(rsi_hypothesis.definition, ("rsi_14",))
        
        validated_evaluations = []
        for evaluation in hypothesis_evaluations:
            validation_result = validation_engine.validate(
                evaluation=evaluation,
                repository=repository,
                hypothesis_registry=hypothesis_registry,
                max_signal_age_hours=24,
            )
            # Update evaluation with validation result
            updated_evaluation = HypothesisEvaluation(
                evaluation_id=evaluation.evaluation_id,
                asset_id=evaluation.asset_id,
                hypothesis_id=evaluation.hypothesis_id,
                hypothesis_version=evaluation.hypothesis_version,
                timestamp=evaluation.timestamp,
                direction=evaluation.direction,
                confidence=evaluation.confidence,
                signals_snapshot_json=evaluation.signals_snapshot_json,
                explanation_json=evaluation.explanation_json,
                generated_trade_idea=evaluation.generated_trade_idea,
                validation_result_json=json.dumps({
                    "is_valid": validation_result.is_valid,
                    "reasons": validation_result.reasons,
                    "metrics": validation_result.metrics,
                    "validated_at": validation_result.validated_at,
                }, sort_keys=True),
                created_at=evaluation.created_at,
            )
            validated_evaluations.append(updated_evaluation)
            repository.persist_hypothesis_evaluation(updated_evaluation)
        
        # Generate trade ideas only from validated evaluations
        validated_outputs = []
        for evaluation in validated_evaluations:
            # Find the original output for this evaluation
            for output in outputs:
                if (output.asset_id == evaluation.asset_id and 
                    output.hypothesis_id == evaluation.hypothesis_id and 
                    output.version == evaluation.hypothesis_version):
                    # Create a copy of output with validation info
                    validated_output = HypothesisOutput(
                        hypothesis_id=output.hypothesis_id,
                        version=output.version,
                        asset_id=output.asset_id,
                        direction=output.direction,
                        horizon=output.horizon,
                        confidence=output.confidence,
                        signals_snapshot=output.signals_snapshot,
                        explanation=output.explanation,
                    )
                    validated_outputs.append(validated_output)
                    break
        
        ideas = generate_trade_ideas(tuple(validated_outputs))
        
        # Update evaluations that resulted in trade ideas
        idea_hypothesis_ids = {idea.hypothesis_id for idea in ideas}
        for evaluation in validated_evaluations:
            if evaluation.hypothesis_id in idea_hypothesis_ids:
                # Create updated evaluation with generated_trade_idea = True
                # Keep the existing validation result
                validation_data = json.loads(evaluation.validation_result_json) if evaluation.validation_result_json else {}
                updated_evaluation = HypothesisEvaluation(
                    evaluation_id=evaluation.evaluation_id,
                    asset_id=evaluation.asset_id,
                    hypothesis_id=evaluation.hypothesis_id,
                    hypothesis_version=evaluation.hypothesis_version,
                    timestamp=evaluation.timestamp,
                    direction=evaluation.direction,
                    confidence=evaluation.confidence,
                    signals_snapshot_json=evaluation.signals_snapshot_json,
                    explanation_json=evaluation.explanation_json,
                    generated_trade_idea=True,
                    validation_result_json=json.dumps(validation_data, sort_keys=True),
                    created_at=evaluation.created_at,
                )
                repository.persist_hypothesis_evaluation(updated_evaluation)
        
        for idea in ideas:
            repository.persist_trade_idea(idea)
        print(json.dumps({"signals": len(signals), "hypotheses": len(outputs), "trade_ideas": len(ideas)}))
        db.close()
        return 0

    if args.command == "review-trade-idea":
        from project.decision.models import Decision
        from uuid import uuid4
        
        # Validate that the trade idea exists
        trade_ideas = repository.get_trade_ideas()
        trade_idea_exists = any(idea.trade_id == args.trade_id for idea in trade_ideas)
        
        if not trade_idea_exists:
            print(json.dumps({"error": f"Trade idea {args.trade_id} not found"}))
            db.close()
            return 1
        
        # Map CLI action to DecisionAction
        action_map = {
            "approve": "approve",
            "reject": "reject",
            "watchlist": "watch"
        }
        action = action_map[args.action]
        
        # Create and persist decision directly
        decision = Decision(
            decision_id=f"decision:{uuid4()}",
            trade_id=args.trade_id,
            action=action,
            structured_reason=args.reason,
            notes=args.notes,
            created_at=utc_now_iso(),
        )
        repository.persist_decision(decision)
        
        print(json.dumps({
            "decision_id": decision.decision_id,
            "trade_id": decision.trade_id,
            "action": decision.action,
            "structured_reason": decision.structured_reason,
            "notes": decision.notes,
            "created_at": decision.created_at,
        }))
        db.close()
        return 0

    # Read-only observability commands (Track 4 - Research Operations Team)
    if args.command == "show-trade-idea":
        from project.common.models import TradeIdea
        import json
        
        # Validate that the trade idea exists
        trade_ideas = repository.get_trade_ideas()
        trade_idea = next((idea for idea in trade_ideas if idea.trade_id == args.trade_id), None)
        
        if not trade_idea:
            print(json.dumps({"error": f"Trade idea {args.trade_id} not found"}))
            db.close()
            return 1
        
        # Output human-readable trade idea details
        print(f"Trade Idea Details:")
        print(f"  Trade ID: {trade_idea.trade_id}")
        print(f"  Asset ID: {trade_idea.asset_id}")
        print(f"  Hypothesis ID: {trade_idea.hypothesis_id}")
        print(f"  Version: {trade_idea.version}")
        print(f"  Direction: {trade_idea.direction}")
        print(f"  Confidence: {trade_idea.confidence:.4f}")
        print(f"  Signals Snapshot:")
        for signal_type, value in trade_idea.signals_snapshot.items():
            print(f"    {signal_type}: {value}")
        db.close()
        return 0

    if args.command == "summarize-batch":
        from project.common.models import HypothesisOutput
        from project.data.models import HypothesisEvaluation
        from project.hypotheses.rsi_mean_reversion import RSIMeanReversionHypothesis
        from project.hypotheses.ma_crossover import MACrossoverHypothesis
        from project.validation.engine import ValidationEngine
        from project.hypotheses.registry import HypothesisRegistry
        from project.trade_engine.generator import generate_trade_ideas
        import json
        import uuid
        
        # Look up the asset to get the correct asset_id (with prefix)
        assets = repository.list_assets()
        asset = next((a for a in assets if a.symbol == args.asset_id.upper()), None)
        if asset is None:
            print(json.dumps({"error": f"Asset {args.asset_id} not found"}))
            db.close()
            return 1
            
        # Run batch logic but only for summarizing (don't persist)
        signals = compute_latest_price_signals(repository, default_signal_registry(), asset.asset_id)
        outputs = evaluate_hypotheses(asset.asset_id, signals, (RSIMeanReversionHypothesis(), MACrossoverHypothesis()))
        
        # Validate hypothesis evaluations
        validation_engine = ValidationEngine()
        hypothesis_registry = HypothesisRegistry()
        rsi_hypothesis = RSIMeanReversionHypothesis()
        hypothesis_registry.register(rsi_hypothesis.definition, ("rsi_14",))
        
        validated_evaluations = []
        for output in outputs:
            # Create temporary evaluation for validation
            evaluation_id = f"eval:{output.asset_id}:{output.hypothesis_id}:{output.version}:{uuid.uuid4()}"
            evaluation = HypothesisEvaluation(
                evaluation_id=evaluation_id,
                asset_id=output.asset_id,
                hypothesis_id=output.hypothesis_id,
                hypothesis_version=output.version,
                timestamp=output.timestamp if hasattr(output, 'timestamp') else utc_now_iso(),
                direction=output.direction,
                confidence=output.confidence,
                signals_snapshot_json=json.dumps(dict(sorted(output.signals_snapshot.items())), sort_keys=True),
                explanation_json=json.dumps(output.explanation, sort_keys=True),
                generated_trade_idea=False,
                validation_result_json=None,
                created_at=utc_now_iso(),
            )
            
            validation_result = validation_engine.validate(
                evaluation=evaluation,
                repository=repository,
                hypothesis_registry=hypothesis_registry,
                max_signal_age_hours=24,
            )
            
            # Update evaluation with validation result
            updated_evaluation = HypothesisEvaluation(
                evaluation_id=evaluation.evaluation_id,
                asset_id=evaluation.asset_id,
                hypothesis_id=evaluation.hypothesis_id,
                hypothesis_version=evaluation.hypothesis_version,
                timestamp=evaluation.timestamp,
                direction=evaluation.direction,
                confidence=evaluation.confidence,
                signals_snapshot_json=evaluation.signals_snapshot_json,
                explanation_json=evaluation.explanation_json,
                generated_trade_idea=evaluation.generated_trade_idea,
                validation_result_json=json.dumps({
                    "is_valid": validation_result.is_valid,
                    "reasons": validation_result.reasons,
                    "metrics": validation_result.metrics,
                    "validated_at": validation_result.validated_at,
                }, sort_keys=True),
                created_at=evaluation.created_at,
            )
            validated_evaluations.append(updated_evaluation)
        
        # Generate trade ideas only from validated evaluations
        validated_outputs = []
        for evaluation in validated_evaluations:
            # Find the original output for this evaluation
            for output in outputs:
                if (output.asset_id == evaluation.asset_id and 
                    output.hypothesis_id == evaluation.hypothesis_id and 
                    output.version == evaluation.hypothesis_version):
                    # Create a copy of output with validation info
                    validated_output = HypothesisOutput(
                        hypothesis_id=output.hypothesis_id,
                        version=output.version,
                        asset_id=output.asset_id,
                        direction=output.direction,
                        horizon=output.horizon,
                        confidence=output.confidence,
                        signals_snapshot=output.signals_snapshot,
                        explanation=output.explanation,
                    )
                    validated_outputs.append(validated_output)
                    break
        
        ideas = generate_trade_ideas(tuple(validated_outputs))
        
        # Print summary (same format as run-batch)
        print(json.dumps({"signals": len(signals), "hypotheses": len(outputs), "trade_ideas": len(ideas)}))
        db.close()
        return 0

    if args.command == "show-hypothesis-evaluations":
        from project.data.models import HypothesisEvaluation
        import json
        
        # Look up the asset to get the correct asset_id (with prefix)
        asset_filter = None
        if getattr(args, 'asset_id', None) is not None:
            assets = repository.list_assets()
            asset = next((a for a in assets if a.symbol == args.asset_id.upper()), None)
            if asset is not None:
                asset_filter = asset.asset_id
        
        # Get hypothesis evaluations, optionally filtered
        evals = repository.get_hypothesis_evaluations(
            asset_id=asset_filter,
            hypothesis_id=getattr(args, 'hypothesis_id', None)
        )
        
        if not evals:
            print("No hypothesis evaluations found matching the criteria.")
            db.close()
            return 0
        
        print(f"Found {len(evals)} hypothesis evaluation(s):")
        print("-" * 80)
        
        for i, evaluation in enumerate(evals, 1):
            print(f"{i}. Evaluation ID: {evaluation.evaluation_id}")
            print(f"   Asset ID: {evaluation.asset_id}")
            print(f"   Hypothesis ID: {evaluation.hypothesis_id} v{evaluation.hypothesis_version}")
            print(f"   Timestamp: {evaluation.timestamp}")
            print(f"   Direction: {evaluation.direction}")
            print(f"   Confidence: {evaluation.confidence:.4f}")
            print(f"   Generated Trade Idea: {evaluation.generated_trade_idea}")
            
            if evaluation.explanation_json:
                try:
                    explanation = json.loads(evaluation.explanation_json)
                    print(f"   Explanation: {explanation}")
                except:
                    print(f"   Explanation: {evaluation.explanation_json[:100]}...")
            
            if evaluation.validation_result_json:
                try:
                    validation = json.loads(evaluation.validation_result_json)
                    print(f"   Validation: valid={validation.get('is_valid')}, reasons={validation.get('reasons', [])}")
                except:
                    print(f"   Validation: {evaluation.validation_result_json[:100]}...")
            
            print()
        
        db.close()
        return 0

    if args.command == "show-validation-failures":
        from project.data.models import HypothesisEvaluation
        import json
        
        # Get all hypothesis evaluations
        evals = repository.get_hypothesis_evaluations()
        
        # Filter to only those with validation failures (not valid or validation shows issues)
        failed_evals = []
        for evaluation in evals:
            if evaluation.validation_result_json:
                try:
                    validation = json.loads(evaluation.validation_result_json)
                    if not validation.get("is_valid", True):
                        failed_evals.append((evaluation, validation))
                except:
                    # If we can't parse validation JSON, treat as failed
                    failed_evals.append((evaluation, {"parse_error": True}))
            # Evaluations without validation results are considered not yet validated
        
        if not failed_evals:
            print("No validation failures found.")
            db.close()
            return 0
        
        print(f"Found {len(failed_evals)} validation failure(s):")
        print("-" * 80)
        
        for i, (evaluation, validation) in enumerate(failed_evals, 1):
            print(f"{i}. Evaluation ID: {evaluation.evaluation_id}")
            print(f"   Asset ID: {evaluation.asset_id}")
            print(f"   Hypothesis ID: {evaluation.hypothesis_id} v{evaluation.hypothesis_version}")
            print(f"   Direction: {evaluation.direction}")
            print(f"   Confidence: {evaluation.confidence:.4f}")
            print(f"   Timestamp: {evaluation.timestamp}")
            
            if "parse_error" in validation:
                print(f"   Validation Parse Error: Could not parse validation result JSON")
            else:
                print(f"   Validation Result:")
                print(f"     Valid: {validation.get('is_valid')}")
                print(f"     Reasons: {validation.get('reasons', [])}")
                print(f"     Validated At: {validation.get('validated_at', 'Unknown')}")
                
                # Show key metrics if available
                metrics = validation.get('metrics', {})
                if metrics:
                    print(f"     Key Metrics:")
                    for key, value in metrics.items():
                        if 'threshold' in key or 'actual' in key or 'age' in key or 'count' in key:
                            print(f"       {key}: {value}")
            
        print()
    
    if args.command == "show-competition":
        print("=== ENTERING SHOW-COMPETITION ===", file=sys.stderr)
        print("=== ENTERING SHOW-COMPETITION (STDOUT) ===", file=sys.stdout)
        print("DEBUG: Inside show-competition condition", file=sys.stderr)
        print("DEBUG: Reached show-competition handler", file=sys.stderr)
        print("DEBUG: show-competition command started", file=sys.stderr); print("DEBUG: About to get hypothesis evaluations", file=sys.stderr)
        from project.data.models import HypothesisEvaluation
        import json
        
        # Get hypothesis evaluations, optionally filtered
        asset_filter = getattr(args, 'asset_id', None)
        print(f"DEBUG: asset_filter from args = {asset_filter}", file=sys.stderr)
        if asset_filter is not None:
            asset_filter = f"asset:{asset_filter.upper()}"
         
        print("!!! REACHED EVALS PROCESSING !!!", file=sys.stderr)
        print(f"DEBUG: asset_filter after formatting = {asset_filter}", file=sys.stderr)
        evals = repository.get_hypothesis_evaluations(
            asset_id=asset_filter
        )
        
        print(f"DEBUG: Got {len(evals)} evaluations", file=sys.stderr)
        print(f"UNIQUE_DEBUG_MARKER: Got {len(evals)} evaluations, type: {type(evals)}", file=sys.stderr)
        print("--- BEFORE UNIQUE MARKER ---", file=sys.stderr)
        print("--- AFTER UNIQUE MARKER ---", file=sys.stderr)
        
        print("UNIQUE_DEBUG_MARKER: About to check if evals is empty", file=sys.stderr)
        if not evals:
            print("No hypothesis evaluations found matching the criteria.")
            db.close()
            return 0
         
        # Group by asset_id and direction to show competition
        from collections import defaultdict
        direction_groups = defaultdict(lambda: defaultdict(list))
        
        for evaluation in evals:
            # Get direction from evaluation
            direction = evaluation.direction
            
            # Apply direction filter if specified
            if hasattr(args, 'direction') and args.direction and args.direction != direction:
                continue
                
            direction_groups[evaluation.asset_id][direction].append(evaluation)
        
        print(f"DEBUG: Direction groups: {dict(direction_groups)}", file=sys.stderr)
        
        if not any(direction_groups[aid] for aid in direction_groups):
            print("No hypothesis evaluations found matching the criteria.")
            db.close()
            return 0
        
        print("Hypothesis Competition Analysis:")
        print("=" * 80)
        
        for asset_id, directions in direction_groups.items():
            print(f"\nAsset ID: {asset_id}")
            print("-" * 40)
            
            for direction, evaluations in directions.items():
                print(f"\n  Direction: {direction}")
                print(f"  Number of competing hypotheses: {len(evaluations)}")
                
                # Sort by confidence (descending)
                sorted_evals = sorted(evaluations, key=lambda x: x.confidence, reverse=True)
                
                for i, evaluation in enumerate(sorted_evals, 1):
                    print(f"\n    #{i} (Rank: {i}, Confidence: {evaluation.confidence:.4f}):")
                    print(f"      Evaluation ID: {evaluation.evaluation_id}")
                    print(f"      Hypothesis ID: {evaluation.hypothesis_id} v{evaluation.hypothesis_version}")
                    print(f"      Timestamp: {evaluation.timestamp}")
                    
                    # Extract competition info from explanation if available
                    if evaluation.explanation_json:
                        try:
                            explanation = json.loads(evaluation.explanation_json)
                            if "competition" in explanation:
                                comp_info = explanation["competition"]
                                print(f"      Is Primary: {comp_info.get('is_primary', 'Unknown')}")
                                print(f"      Competing Hypotheses: {comp_info.get('competing_hypotheses_count', 0)}")
                        except:
                            pass
                    
                    # Show validation status
                    if evaluation.validation_result_json:
                        try:
                            validation = json.loads(evaluation.validation_result_json)
                            print(f"      Validation: {'PASS' if validation.get('is_valid') else 'FAIL'}")
                            if not validation.get('is_valid', True):
                                print(f"      Rejection Reasons: {', '.join(validation.get('reasons', []))}")
                        except:
                            print(f"      Validation: PARSE ERROR")
                    else:
                        print(f"      Validation: NOT YET VALIDATED")
                        
                    # Show explanation summary
                    if evaluation.explanation_json:
                        try:
                            explanation = json.loads(evaluation.explanation_json)
                            if "confidence_factors" in explanation:
                                cf = explanation["confidence_factors"]
                                print(f"      Confidence Base: {cf.get('base_confidence', 0):.4f}")
                                print(f"      Signal Agreement: {cf.get('signal_agreement', 0):.4f}")
                        except:
                            pass
                        
        db.close()
        return 0

    if args.command == "show-explanation":
        from project.data.models import HypothesisEvaluation
        import json
        
        # Look up the asset to get the correct asset_id (with prefix)
        # Note: show-explanation doesn't filter by asset_id, it filters by evaluation_id directly
        
        # Get the specific evaluation
        evals = repository.get_hypothesis_evaluations()
        evaluation = next((e for e in evals if e.evaluation_id == args.evaluation_id), None)
        
        if not evaluation:
            print(f"Error: Evaluation {args.evaluation_id} not found")
            db.close()
            return 1
        
        print(f"Explanation for Evaluation: {evaluation.evaluation_id}")
        print("=" * 80)
        
        print(f"Asset ID: {evaluation.asset_id}")
        print(f"Hypothesis ID: {evaluation.hypothesis_id} v{evaluation.hypothesis_version}")
        print(f"Direction: {evaluation.direction}")
        print(f"Confidence: {evaluation.confidence:.4f}")
        print(f"Timestamp: {evaluation.timestamp}")
        print(f"Generated Trade Idea: {evaluation.generated_trade_idea}")
        
        # Show signals snapshot
        if evaluation.signals_snapshot_json:
            try:
                signals = json.loads(evaluation.signals_snapshot_json)
                print(f"\nSignals Snapshot:")
                for signal_type, value in sorted(signals.items()):
                    print(f"  {signal_type}: {value:.4f}")
            except:
                print(f"\nSignals Snapshot: {evaluation.signals_snapshot_json}")
        
        # Show explanation
        if evaluation.explanation_json:
            try:
                explanation = json.loads(evaluation.explanation_json)
                print(f"\nExplanation:")
                print(json.dumps(explanation, indent=2))
            except:
                print(f"\nExplanation: {evaluation.explanation_json}")
        
        # Show validation result
        if evaluation.validation_result_json:
            try:
                validation = json.loads(evaluation.validation_result_json)
                print(f"\nValidation Result:")
                print(f"  Valid: {validation.get('is_valid')}")
                print(f"  Reasons: {validation.get('reasons', [])}")
                print(f"  Validated At: {validation.get('validated_at', 'Unknown')}")
                if validation.get('metrics'):
                    print(f"  Metrics:")
                    for key, value in sorted(validation['metrics'].items()):
                        print(f"    {key}: {value}")
            except:
                print(f"\nValidation Result: {evaluation.validation_result_json}")
        else:
            print(f"\nValidation Result: NOT YET VALIDATED")
        
        db.close()
        return 0

    if args.command == "show-signal-lineage":
        from project.data.models import HypothesisEvaluation
        import json
        from collections import defaultdict
        
        # Get all evaluations for the asset
        evals = repository.get_hypothesis_evaluations(asset_id=args.asset_id)
        
        if not evals:
            print(f"No hypothesis evaluations found for asset {args.asset_id}")
            db.close()
            return 0
        
        print(f"Signal Lineage for Asset: {args.asset_id}")
        print("=" * 80)
        
        # Group by timestamp to show signal evolution over time
        timestamp_groups = defaultdict(list)
        for evaluation in evals:
            timestamp_groups[evaluation.timestamp].append(evaluation)
        
        # Sort timestamps
        sorted_timestamps = sorted(timestamp_groups.keys())
        
        for timestamp in sorted_timestamps:
            evaluations = timestamp_groups[timestamp]
            print(f"\nTimestamp: {timestamp}")
            print("-" * 40)
            
            for evaluation in evaluations:
                print(f"\n  Evaluation ID: {evaluation.evaluation_id}")
                print(f"  Hypothesis: {evaluation.hypothesis_id} v{evaluation.hypothesis_version}")
                print(f"  Direction: {evaluation.direction}")
                print(f"  Confidence: {evaluation.confidence:.4f}")
                
                # Show signals
                if evaluation.signals_snapshot_json:
                    try:
                        signals = json.loads(evaluation.signals_snapshot_json)
                        print(f"  Signals:")
                        for signal_type, value in sorted(signals.items()):
                            print(f"    {signal_type}: {value:.4f}")
                    except:
                        print(f"  Signals: {evaluation.signals_snapshot_json}")
                        
                # Show explanation highlights
                if evaluation.explanation_json:
                    try:
                        explanation = json.loads(evaluation.explanation_json)
                        if "triggering_signals" in explanation and explanation["triggering_signals"]:
                            print(f"  Triggering Signals:")
                            for signal in explanation["triggering_signals"]:
                                print(f"    {signal.get('signal_type', 'Unknown')}: {signal.get('interpretation', 'No interpretation')}")
                        elif "supporting_signals" in explanation and explanation["supporting_signals"]:
                            print(f"  Supporting Signals:")
                            for signal in explanation["supporting_signals"]:
                                print(f"    {signal.get('signal_type', 'Unknown')}: {signal.get('interpretation', 'No interpretation')}")
                        elif "contradicting_signals" in explanation and explanation["contradicting_signals"]:
                            print(f"  Contradicting Signals:")
                            for signal in explanation["contradicting_signals"]:
                                print(f"    {signal.get('signal_type', 'Unknown')}: {signal.get('interpretation', 'No interpretation')}")
                    except:
                        pass
        
        db.close()
        return 0

    if args.command == "show-validation-path":
        from project.data.models import HypothesisEvaluation
        import json
        
        # Get the specific evaluation
        evals = repository.get_hypothesis_evaluations()
        evaluation = next((e for e in evals if e.evaluation_id == args.evaluation_id), None)
        
        if not evaluation:
            print(f"Error: Evaluation {args.evaluation_id} not found")
            db.close()
            return 1
        
        print(f"Validation Path for Evaluation: {evaluation.evaluation_id}")
        print("=" * 80)
        
        print(f"Asset ID: {evaluation.asset_id}")
        print(f"Hypothesis ID: {evaluation.hypothesis_id} v{evaluation.hypothesis_version}")
        print(f"Direction: {evaluation.direction}")
        print(f"Confidence: {evaluation.confidence:.4f}")
        print(f"Timestamp: {evaluation.timestamp}")
        
        # Show validation result
        if evaluation.validation_result_json:
            try:
                validation = json.loads(evaluation.validation_result_json)
                print(f"\nValidation Result:")
                print(f"  Overall: {'PASS' if validation.get('is_valid') else 'FAIL'}")
                print(f"  Reasons: {validation.get('reasons', [])}")
                print(f"  Validated At: {validation.get('validated_at', 'Unknown')}")
                
                if validation.get('metrics'):
                    print(f"\nValidation Metrics (by validator):")
                    # Group metrics by validator
                    validator_metrics = defaultdict(dict)
                    for key, value in validation['metrics'].items():
                        if '.' in key:
                            validator, metric = key.split('.', 1)
                            validator_metrics[validator][metric] = value
                        else:
                            validator_metrics['general'][key] = value
                    
                    for validator, metrics in sorted(validator_metrics.items()):
                        print(f"\n  {validator}:")
                        for metric, value in sorted(metrics.items()):
                            print(f"    {metric}: {value}")
            except:
                print(f"\nValidation Result: {evaluation.validation_result_json}")
        else:
            print(f"\nValidation Result: NOT YET VALIDATED")
        
        db.close()
        return 0

    if args.command == "list-rejected-hypotheses":
        from project.data.models import HypothesisEvaluation
        import json
        
        # Get all hypothesis evaluations
        evals = repository.get_hypothesis_evaluations()
        
        # Filter to only those that were rejected (validation failed)
        rejected_evals = []
        for evaluation in evals:
            if evaluation.validation_result_json:
                try:
                    validation = json.loads(evaluation.validation_result_json)
                    if not validation.get("is_valid", True):
                        rejected_evals.append((evaluation, validation))
                except:
                    # If we can't parse validation JSON, treat as failed/rejected
                    rejected_evals.append((evaluation, {"parse_error": True, "reasons": ["invalid_json"]}))
        
        if not rejected_evals:
            print("No rejected hypotheses found.")
            db.close()
            return 0
        
        print(f"List of Rejected Hypotheses ({len(rejected_evals)} total):")
        print("=" * 80)
        
        # Sort by timestamp (newest first)
        rejected_evals.sort(key=lambda x: x[0].timestamp, reverse=True)
        
        for i, (evaluation, validation) in enumerate(rejected_evals, 1):
            print(f"\n{i}. Evaluation ID: {evaluation.evaluation_id}")
            print(f"   Asset ID: {evaluation.asset_id}")
            print(f"   Hypothesis ID: {evaluation.hypothesis_id} v{evaluation.hypothesis_version}")
            print(f"   Direction: {evaluation.direction}")
            print(f"   Confidence: {evaluation.confidence:.4f}")
            print(f"   Timestamp: {evaluation.timestamp}")
            
            if "parse_error" in validation:
                print(f"   Rejection Reason: Validation result could not be parsed")
            else:
                reasons = validation.get('reasons', [])
                print(f"   Rejection Reasons: {', '.join(reasons) if reasons else 'Unknown'}")
                
                # Show specific metrics that led to rejection
                if validation.get('metrics'):
                    print(f"   Rejection Details:")
                    for key, value in validation['metrics'].items():
                        if 'threshold' in key or 'actual' in key or 'age' in key or 'count' in key or 'error' in key:
                            print(f"     {key}: {value}")
        
        db.close()
        return 0

    if args.command == "report-hypotheses":
        from project.data.models import SignalEvaluation
        from project.learning.engine import aggregate_signal_performance
        from collections import defaultdict
        
        evals = repository.get_signal_evaluations()
        if not evals:
            print("No signal evaluations found.")
            db.close()
            return 0
            
        # Group by hypothesis_id
        grouped = defaultdict(list)
        for e in evals:
            grouped[e.hypothesis_id].append(e)
            
        horizon_map = {1: 0, 5: 1, 20: 2}
        horizon_idx = horizon_map.get(args.horizon, 2)
        
        print(f"Hypothesis Performance Report (Horizon: {args.horizon} bars)")
        print("=" * 80)
        print(f"{'Hypothesis ID':<30} {'Signals':<10} {'Hit Rate':<10} {'Mean Ret':<10} {'Sharpe':<10}")
        print("-" * 80)
        
        for hyp_id, hyp_evals in sorted(grouped.items()):
            metrics = aggregate_signal_performance(hyp_evals, horizon_idx=horizon_idx)
            print(f"{hyp_id:<30} {metrics.n_signals:<10} {metrics.hit_rate:<10.4f} {metrics.mean_return:<10.4f} {metrics.sharpe_like_score:<10.4f}")
            
        db.close()
        return 0

    if args.command == "backtest-hypothesis":
        from project.backtesting.engine import BacktestEngine
        from project.backtesting.models import BacktestConfig
        from datetime import datetime
        
        try:
            start_dt = datetime.strptime(args.start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(args.end_date, "%Y-%m-%d")
        except ValueError as e:
            print(f"Error parsing dates: {e}. Expected format YYYY-MM-DD")
            db.close()
            return 1
            
        engine = BacktestEngine(repository)
        config = BacktestConfig()
        
        print(f"Running backtest for {args.hypothesis_id} on {args.asset_symbol}...")
        print(f"Period: {args.start_date} to {args.end_date}")
        print("-" * 40)
        
        try:
            result = engine.run(
                hypothesis_id=args.hypothesis_id,
                asset_symbol=args.asset_symbol,
                start_timestamp=start_dt,
                end_timestamp=end_dt,
                config=config
            )
            
            print(f"Backtest Result for {result.hypothesis_id}:")
            print(f"  Total Trades: {result.total_trades}")
            print(f"  Win Rate:     {result.win_rate:.2%}")
            print(f"  Total PnL:    ${result.total_pnl:,.2f}")
            print(f"  Mean PnL:     ${result.mean_pnl:,.2f}")
            print(f"  Max Drawdown: ${result.max_drawdown:,.2f}")
            print(f"  Sharpe Ratio: {result.sharpe_ratio:.4f}")
            print(f"  Total Return: {result.total_return_pct:.2%}")
            
        except Exception as e:
            print(f"Backtest failed: {e}")
            db.close()
            return 1
            
        db.close()
        return 0

    db.close()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())