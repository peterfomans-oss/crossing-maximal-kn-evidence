"""Crash-resumable native-XOR runner for the crossing-only SAT model.

The base formula is partitioned by fixing one of the three crossing choices on
each of several K4s.  These cubes are mutually exclusive and exhaustive because
the direct encoding enforces exactly one choice on every K4.  Each completed
cube is written atomically, so a later invocation can rebuild the same formula
and skip work that was already completed.

The checkpoint files are a reproducible solver audit, not an independently
checkable UNSAT proof certificate.  SAT models are checked against every CNF
and XOR clause before both the Boolean assignment and the readable crossing
pattern are saved.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import platform
import socket
import sys
import threading
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pycryptosat

from crossing_model_explore import normalized_pair
from crossing_parity_sat import build_instance
from sparse_parity_basis import matching_edges


SCHEMA_VERSION = 2
SOLVER_NAME = "cryptominisat-native-xor"
ROOT = Path(__file__).resolve().parent
STOP_REQUEST_NAME = "stop-request.json"
ENCODER_FILES = (
    "crossing_parity_sat.py",
    "crossing_model_explore.py",
    "sparse_parity_basis.py",
    "cm5_unlabeled.json0",
    "crossing_parity_checkpoint.py",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def atomic_write_json(path: Path, value: Any) -> None:
    """Write one complete JSON value and atomically replace the destination."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as output:
            json.dump(value, output, ensure_ascii=False, indent=2, sort_keys=True)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as source:
        return json.load(source)


def formula_sha256(cnf, xor_clauses) -> str:
    """Hash the ordered formula without constructing a second serialized copy."""
    digest = hashlib.sha256()
    digest.update(b"crossing-parity-formula-v1\n")
    for clause in cnf.clauses:
        digest.update(b"C ")
        digest.update(" ".join(map(str, clause)).encode("ascii"))
        digest.update(b" 0\n")
    for variables, rhs in xor_clauses:
        digest.update(b"X1 " if rhs else b"X0 ")
        digest.update(" ".join(map(str, variables)).encode("ascii"))
        digest.update(b" 0\n")
    return digest.hexdigest()


def current_file_inventory() -> dict[str, str]:
    inventory = {}
    for name in ENCODER_FILES:
        path = ROOT / name
        if not path.is_file():
            raise FileNotFoundError(path)
        inventory[name] = sha256_file(path)
    return inventory


def solver_inventory() -> dict[str, Any]:
    binding_path = Path(pycryptosat.__file__).resolve()
    return {
        "name": SOLVER_NAME,
        "version": getattr(pycryptosat, "__version__", "unknown"),
        "binding_filename": binding_path.name,
        "binding_size_bytes": binding_path.stat().st_size,
        "binding_sha256": sha256_file(binding_path),
        "python_version": sys.version,
        "python_executable_filename": Path(sys.executable).name,
        "python_executable_sha256": sha256_file(Path(sys.executable)),
    }


def quarantine_orphan_temp_files(run_dir: Path) -> list[Path]:
    """Preserve incomplete atomic-write files left behind by a hard kill."""
    candidates = [
        path
        for path in run_dir.rglob(".*.tmp")
        if "orphaned-temp" not in path.parts and path.is_file()
    ]
    moved = []
    if not candidates:
        return moved
    destination = run_dir / "orphaned-temp"
    destination.mkdir(parents=True, exist_ok=True)
    for path in candidates:
        relative = path.relative_to(run_dir)
        safe_name = "__".join(relative.parts)
        target = destination / f"{safe_timestamp()}-{uuid.uuid4().hex[:8]}-{safe_name}"
        os.replace(path, target)
        moved.append(target)
    return moved


def process_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if pid == os.getpid():
        return True
    if os.name == "nt":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        synchronize = 0x00100000
        query_limited_information = 0x1000
        handle = kernel32.OpenProcess(
            synchronize | query_limited_information, False, pid
        )
        if not handle:
            # Access denied means a process with this PID exists, so fail safe.
            return kernel32.GetLastError() == 5
        try:
            exit_code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return True
            return exit_code.value == 259  # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class RunLock:
    """Single-process lock with conservative stale-lock recovery."""

    def __init__(self, run_dir: Path):
        self.path = run_dir / "run-lock.json"
        self.token = uuid.uuid4().hex
        self.info = {
            "schema_version": SCHEMA_VERSION,
            "pid": os.getpid(),
            "hostname": socket.gethostname(),
            "started_utc": utc_now(),
            "token": self.token,
        }

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(3):
            try:
                with self.path.open("x", encoding="utf-8", newline="\n") as output:
                    json.dump(self.info, output, ensure_ascii=False, indent=2, sort_keys=True)
                    output.write("\n")
                    output.flush()
                    os.fsync(output.fileno())
                return
            except FileExistsError:
                try:
                    previous = load_json(self.path)
                    previous_pid = int(previous.get("pid", -1))
                except Exception as exc:
                    raise RuntimeError(
                        f"cannot parse existing lock {self.path}: {exc}"
                    ) from exc
                if process_is_alive(previous_pid):
                    raise RuntimeError(
                        f"another runner is active with PID {previous_pid}; "
                        "do not start a duplicate K17 process"
                    )
                stale = self.path.with_name(
                    f"run-lock.stale-{safe_timestamp()}-{uuid.uuid4().hex[:8]}.json"
                )
                os.replace(self.path, stale)
        raise RuntimeError(f"could not acquire run lock {self.path}")

    def release(self) -> None:
        try:
            current = load_json(self.path)
        except Exception:
            # Never mask the real error or delete an unreadable/foreign lock.
            return
        if isinstance(current, dict) and current.get("token") == self.token:
            self.path.unlink()


class StatusWriter:
    def __init__(self, path: Path, interval_seconds: float, initial: dict[str, Any]):
        self.path = path
        self.interval_seconds = interval_seconds
        self.data = dict(initial)
        self.lock = threading.Lock()
        self.write_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None

    def _snapshot(self) -> dict[str, Any]:
        with self.lock:
            snapshot = dict(self.data)
        snapshot["heartbeat_utc"] = utc_now()
        return snapshot

    def write(self) -> None:
        # Serialize heartbeat and main-thread writes so an older snapshot can
        # never overwrite a newer state transition.
        with self.write_lock:
            atomic_write_json(self.path, self._snapshot())

    def update(self, **changes: Any) -> None:
        with self.lock:
            self.data.update(changes)
        self.write()

    def start(self) -> None:
        self.write()
        if self.interval_seconds <= 0:
            return

        def worker() -> None:
            while not self.stop_event.wait(self.interval_seconds):
                try:
                    self.write()
                except Exception:
                    # The main process performs all correctness-critical writes.
                    pass

        self.thread = threading.Thread(target=worker, name="checkpoint-heartbeat", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=2)


def serialize_pair(pair) -> list[list[int]]:
    return [list(pair[0]), list(pair[1])]


# These K4s deliberately avoid the induction-witness vertices 0, 1, 2 and
# spread the split variables across K17.  Prefixes also make useful small-K
# tests: one group at K8 and three groups at K12.
BALANCED_CUBE_QUADS = (
    (3, 4, 5, 6),
    (3, 7, 8, 9),
    (4, 7, 10, 11),
    (5, 8, 10, 12),
    (6, 9, 11, 12),
    (13, 14, 15, 16),
)


def choose_cube_groups(
    n: int,
    depth: int,
    crossing_vars: dict,
    cnf,
) -> list[dict[str, Any]]:
    if depth < 0 or depth > 8:
        raise ValueError("cube depth must be between 0 and 8")
    unit_variables = {
        abs(clause[0]) for clause in cnf.clauses if len(clause) == 1
    }
    candidates = []
    for quad in itertools.combinations(range(n), 4):
        pairs = [normalized_pair(*pair) for pair in matching_edges(quad)]
        literals = [crossing_vars[pair] for pair in pairs]
        if any(literal in unit_variables for literal in literals):
            continue
        candidates.append((quad, pairs, literals))
    if len(candidates) < depth:
        raise ValueError(
            f"only {len(candidates)} unfixed K4 groups are available for depth {depth}"
        )

    candidate_by_quad = {item[0]: item for item in candidates}
    vertex_use = [0] * n
    selected = []
    remaining = list(candidates)
    for preferred_quad in BALANCED_CUBE_QUADS:
        if len(selected) >= depth:
            break
        item = candidate_by_quad.get(preferred_quad)
        if item is None:
            continue
        remaining.remove(item)
        quad, pairs, literals = item
        for vertex in quad:
            vertex_use[vertex] += 1
        selected.append((quad, pairs, literals))

    while len(selected) < depth:
        quad, pairs, literals = min(
            remaining,
            key=lambda item: (
                max(vertex_use[vertex] for vertex in item[0]),
                sum(vertex_use[vertex] for vertex in item[0]),
                item[0],
            ),
        )
        remaining.remove((quad, pairs, literals))
        for vertex in quad:
            vertex_use[vertex] += 1
        selected.append((quad, pairs, literals))

    groups = []
    for group_index, (quad, pairs, literals) in enumerate(selected):
        groups.append(
            {
                "group_index": group_index,
                "quad": list(quad),
                "choices": [
                    {
                        "choice": choice,
                        "literal": literal,
                        "crossing_edges": serialize_pair(pair),
                    }
                    for choice, (pair, literal) in enumerate(zip(pairs, literals, strict=True))
                ],
            }
        )
    return groups


def cube_digits(index: int, depth: int) -> list[int]:
    digits = [0] * depth
    value = index
    for position in range(depth - 1, -1, -1):
        digits[position] = value % 3
        value //= 3
    if value:
        raise ValueError(index)
    return digits


def cube_assumptions(groups: list[dict[str, Any]], index: int) -> tuple[list[int], list[int]]:
    digits = cube_digits(index, len(groups))
    assumptions = []
    for group, selected_choice in zip(groups, digits, strict=True):
        for choice in group["choices"]:
            literal = int(choice["literal"])
            assumptions.append(literal if choice["choice"] == selected_choice else -literal)
    return digits, assumptions


def cube_semantics(groups: list[dict[str, Any]], digits: list[int]) -> list[dict[str, Any]]:
    result = []
    for group, selected_choice in zip(groups, digits, strict=True):
        selected = group["choices"][selected_choice]
        result.append(
            {
                "group_index": group["group_index"],
                "quad": group["quad"],
                "selected_choice": selected_choice,
                "selected_literal": selected["literal"],
                "selected_crossing_edges": selected["crossing_edges"],
            }
        )
    return result


def build_partition(
    n: int,
    depth: int,
    formula_hash: str,
    crossing_vars: dict,
    cnf,
) -> dict[str, Any]:
    groups = choose_cube_groups(n, depth, crossing_vars, cnf)
    if [group["group_index"] for group in groups] != list(range(depth)):
        raise RuntimeError("partition group indices are not consecutive")
    if len({tuple(group["quad"]) for group in groups}) != depth:
        raise RuntimeError("partition repeats a K4 group")

    clause_set = {tuple(sorted(map(int, clause))) for clause in cnf.clauses}
    all_group_variables = []
    for group in groups:
        quad = tuple(group["quad"])
        expected_pairs = [normalized_pair(*pair) for pair in matching_edges(quad)]
        choices = group["choices"]
        if [choice["choice"] for choice in choices] != [0, 1, 2]:
            raise RuntimeError(f"partition K4 {quad} has invalid choice numbering")
        expected_literals = [crossing_vars[pair] for pair in expected_pairs]
        actual_literals = [int(choice["literal"]) for choice in choices]
        if actual_literals != expected_literals:
            raise RuntimeError(f"partition K4 {quad} has invalid SAT variables")
        if [choice["crossing_edges"] for choice in choices] != [
            serialize_pair(pair) for pair in expected_pairs
        ]:
            raise RuntimeError(f"partition K4 {quad} has invalid crossing labels")
        if tuple(sorted(actual_literals)) not in clause_set:
            raise RuntimeError(f"partition K4 {quad} lacks its at-least-one clause")
        for first, second in itertools.combinations(actual_literals, 2):
            if tuple(sorted((-first, -second))) not in clause_set:
                raise RuntimeError(f"partition K4 {quad} lacks an at-most-one clause")
        all_group_variables.extend(actual_literals)
    if len(set(all_group_variables)) != len(all_group_variables):
        raise RuntimeError("partition groups unexpectedly share SAT variables")

    total = 3**depth
    enumeration_digest = hashlib.sha256()
    enumeration_digest.update(b"crossing-k4-cubes-enumeration-v1\n")
    seen_digits = set()
    seen_assumptions = set()
    for index in range(total):
        digits, assumptions = cube_assumptions(groups, index)
        digits_key = tuple(digits)
        assumptions_key = tuple(assumptions)
        if digits_key in seen_digits or assumptions_key in seen_assumptions:
            raise RuntimeError("partition cube enumeration is not unique")
        if len(assumptions) != 3 * depth:
            raise RuntimeError("partition cube is not full one-hot")
        if any(-literal in assumptions for literal in assumptions):
            raise RuntimeError("partition cube has contradictory assumptions")
        seen_digits.add(digits_key)
        seen_assumptions.add(assumptions_key)
        enumeration_digest.update(
            json.dumps(
                {"index": index, "digits": digits, "assumptions": assumptions},
                sort_keys=True,
                separators=(",", ":"),
            ).encode("ascii")
        )
        enumeration_digest.update(b"\n")
    expected_digits = set(itertools.product(range(3), repeat=depth))
    if seen_digits != expected_digits:
        raise RuntimeError("partition does not exhaust every ternary choice tuple")

    partition = {
        "kind": "exhaustive-k4-ternary-cubes",
        "protocol": "base3-lexicographic-full-one-hot-v1",
        "coverage_reason": (
            "Each selected K4 has exactly one of its three crossing literals true; "
            "all 3^depth full one-hot combinations are disjoint and exhaustive."
        ),
        "depth": depth,
        "total_cubes": total,
        "groups": groups,
        "mechanical_audit": {
            "checked_groups": depth,
            "checked_cubes": total,
            "one_hot_literals_per_cube": 3 * depth,
            "enumeration_sha256": enumeration_digest.hexdigest(),
            "exact_one_clauses_found": True,
        },
    }
    partition["sha256"] = canonical_json_sha256(
        {
            "domain": "crossing-k4-partition-v1",
            "formula_sha256": formula_hash,
            "partition": partition,
        }
    )
    return partition


def cube_path(run_dir: Path, index: int, total: int) -> Path:
    width = max(3, len(str(max(total - 1, 0))))
    return run_dir / "cubes" / f"cube-{index:0{width}d}.json"


def formula_counts(stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "n": stats["n"],
        "variables": stats["variables"],
        "cnf_clauses": stats["clauses"],
        "xor_clauses": stats["xor_clauses"],
        "basis_dimension": stats["basis_dimension"],
        "max_crossing_basis_width": stats["max_crossing_basis_width"],
    }


def runner_config(args) -> dict[str, Any]:
    return {
        "n": args.n,
        "induction_witness": args.induction_witness,
        "all_deletion_witnesses": args.all_deletion_witnesses,
        "k5_encoding": args.k5_encoding,
        "parity_encoding": args.parity_encoding,
        "native_xor": True,
        "threads": args.threads,
        "cube_depth": args.cube_depth,
    }


def load_or_create_manifest(
    run_dir: Path,
    config: dict[str, Any],
    counts: dict[str, Any],
    formula_hash: str,
    files: dict[str, str],
    crossing_vars: dict,
    cnf,
) -> dict[str, Any]:
    manifest_path = run_dir / "manifest.json"
    solver = solver_inventory()
    partition = build_partition(
        config["n"],
        config["cube_depth"],
        formula_hash,
        crossing_vars,
        cnf,
    )
    if manifest_path.exists():
        manifest = load_json(manifest_path)
        expected = {
            "schema_version": SCHEMA_VERSION,
            "config": config,
            "formula": {**counts, "sha256": formula_hash},
            "files": files,
            "solver": solver,
            "partition": partition,
        }
        for key, value in expected.items():
            if manifest.get(key) != value:
                raise RuntimeError(
                    f"checkpoint mismatch in {key}; refusing to mix different code, "
                    "settings, formulas, or solver versions"
                )
        return manifest

    unexpected = [
        path.name
        for path in run_dir.iterdir()
        if path.name not in {"run-lock.json", "orphaned-temp"}
        and not path.name.startswith("run-lock.stale-")
    ]
    if unexpected:
        raise RuntimeError(
            f"run directory has no manifest but is not empty: {sorted(unexpected)}"
        )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "run_id": uuid.uuid4().hex,
        "created_utc": utc_now(),
        "config": config,
        "formula": {**counts, "sha256": formula_hash},
        "files": files,
        "solver": solver,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "hostname_at_creation": socket.gethostname(),
        },
        "partition": partition,
    }
    atomic_write_json(manifest_path, manifest)
    return manifest


def validate_cube_record(
    record: dict[str, Any],
    manifest: dict[str, Any],
    index: int,
) -> None:
    groups = manifest["partition"]["groups"]
    digits, assumptions = cube_assumptions(groups, index)
    expected = {
        "schema_version": SCHEMA_VERSION,
        "run_id": manifest["run_id"],
        "formula_sha256": manifest["formula"]["sha256"],
        "partition_sha256": manifest["partition"]["sha256"],
        "cube_index": index,
        "choices": digits,
        "assumptions": assumptions,
        "assumption_semantics": cube_semantics(groups, digits),
    }
    for key, value in expected.items():
        if record.get(key) != value:
            raise RuntimeError(f"invalid checkpoint cube {index}: mismatch in {key}")
    if record.get("result") not in {"SAT", "UNSAT"}:
        raise RuntimeError(f"invalid checkpoint cube {index}: bad result")
    if record.get("solver") != manifest["solver"]:
        raise RuntimeError(f"invalid checkpoint cube {index}: solver fingerprint mismatch")
    if record.get("result") == "UNSAT":
        diagnostic = record.get("diagnostic_conflict")
        if not isinstance(diagnostic, dict):
            raise RuntimeError(f"invalid checkpoint cube {index}: missing conflict diagnostic")
        clause = diagnostic.get("solver_reported_blocking_clause")
        if not isinstance(clause, list) or not all(
            isinstance(literal, int) and -literal in assumptions for literal in clause
        ):
            raise RuntimeError(f"invalid checkpoint cube {index}: malformed blocking clause")
        if diagnostic.get("is_proof_certificate") is not False:
            raise RuntimeError(f"invalid checkpoint cube {index}: bad proof disclaimer")
    elif not isinstance(record.get("sat_model"), dict):
        raise RuntimeError(f"invalid checkpoint cube {index}: missing SAT model metadata")


def load_completed_cubes(run_dir: Path, manifest: dict[str, Any]) -> dict[int, dict[str, Any]]:
    total = manifest["partition"]["total_cubes"]
    completed = {}
    cubes_dir = run_dir / "cubes"
    if not cubes_dir.exists():
        return completed
    for path in sorted(cubes_dir.glob("cube-*.json")):
        record = load_json(path)
        index = int(record.get("cube_index", -1))
        if not 0 <= index < total:
            raise RuntimeError(f"invalid cube index in {path}")
        if path != cube_path(run_dir, index, total):
            raise RuntimeError(f"misnamed cube checkpoint {path}")
        if index in completed:
            raise RuntimeError(f"duplicate checkpoint for cube {index}")
        validate_cube_record(record, manifest, index)
        completed[index] = record
    return completed


def bool_value(model: list[bool], literal: int) -> bool:
    value = model[abs(literal)]
    return value if literal > 0 else not value


def verify_model(cnf, xor_clauses, model: list[bool], assumptions: list[int]) -> dict[str, Any]:
    for literal in assumptions:
        if not bool_value(model, literal):
            raise RuntimeError(f"SAT model violates cube assumption {literal}")
    for index, clause in enumerate(cnf.clauses):
        if not any(bool_value(model, literal) for literal in clause):
            raise RuntimeError(f"SAT model violates CNF clause {index}")
    for index, (variables, rhs) in enumerate(xor_clauses):
        parity = sum(model[variable] for variable in variables) % 2
        if parity != int(rhs):
            raise RuntimeError(f"SAT model violates XOR clause {index}")
    return {
        "assumptions_checked": len(assumptions),
        "cnf_clauses_checked": len(cnf.clauses),
        "xor_clauses_checked": len(xor_clauses),
        "verified": True,
    }


def normalize_solution(solution, variable_count: int) -> list[bool]:
    if solution is None or len(solution) <= variable_count:
        raise RuntimeError("solver returned an incomplete SAT model")
    model = [False] * (variable_count + 1)
    for variable in range(1, variable_count + 1):
        value = solution[variable]
        if not isinstance(value, bool):
            raise RuntimeError(f"solver did not assign variable {variable}")
        model[variable] = value
    return model


def crossing_pattern(n: int, crossing_vars: dict, model: list[bool]) -> dict[str, Any]:
    choices = []
    crossings = []
    edge_crossing_counts = {
        f"{first}-{second}": 0 for first, second in itertools.combinations(range(n), 2)
    }
    for quad in itertools.combinations(range(n), 4):
        pairs = [normalized_pair(*pair) for pair in matching_edges(quad)]
        hits = [choice for choice, pair in enumerate(pairs) if model[crossing_vars[pair]]]
        if len(hits) != 1:
            raise RuntimeError(f"SAT model has {len(hits)} crossing choices on K4 {quad}")
        choice = hits[0]
        pair = pairs[choice]
        for edge in pair:
            edge_crossing_counts[f"{edge[0]}-{edge[1]}"] += 1
        choices.append(choice)
        crossings.append(
            {
                "quad": list(quad),
                "choice": choice,
                "variable": crossing_vars[pair],
                "crossing_edges": serialize_pair(pair),
            }
        )
    return {
        "n": n,
        "k4_order": "lexicographic combinations(range(n), 4)",
        "choice_order": "(ab|cd, ac|bd, ad|bc) for a<b<c<d",
        "total_crossings": len(crossings),
        "minimum_edge_crossings": min(edge_crossing_counts.values()),
        "edge_crossing_counts": edge_crossing_counts,
        "choices": choices,
        "crossings": crossings,
    }


def aggregate_cube_hash(run_dir: Path, total: int) -> str:
    digest = hashlib.sha256()
    digest.update(b"crossing-parity-cube-audit-v1\n")
    for index in range(total):
        path = cube_path(run_dir, index, total)
        digest.update(f"{index}:".encode("ascii"))
        digest.update(sha256_file(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def save_sat_result(
    run_dir: Path,
    manifest: dict[str, Any],
    cube_record: dict[str, Any],
    solution,
    cnf,
    xor_clauses,
    crossing_vars: dict,
) -> dict[str, Any]:
    variable_count = manifest["formula"]["variables"]
    model = normalize_solution(solution, variable_count)
    validation = verify_model(cnf, xor_clauses, model, cube_record["assumptions"])
    pattern = crossing_pattern(manifest["config"]["n"], crossing_vars, model)

    model_path = run_dir / "sat-model.json"
    pattern_path = run_dir / "sat-crossing-pattern.json"
    atomic_write_json(
        model_path,
        {
            "schema_version": SCHEMA_VERSION,
            "run_id": manifest["run_id"],
            "formula_sha256": manifest["formula"]["sha256"],
            "partition_sha256": manifest["partition"]["sha256"],
            "variable_count": variable_count,
            "assignment_encoding": (
                "Variables listed in true_variables are true; every other variable "
                "from 1 through variable_count is false."
            ),
            "true_variables": [
                variable for variable in range(1, variable_count + 1) if model[variable]
            ],
            "validation": validation,
        },
    )
    atomic_write_json(
        pattern_path,
        {
            "schema_version": SCHEMA_VERSION,
            "run_id": manifest["run_id"],
            "formula_sha256": manifest["formula"]["sha256"],
            "partition_sha256": manifest["partition"]["sha256"],
            **pattern,
        },
    )
    cube_record["sat_model"] = {
        "path": model_path.name,
        "sha256": sha256_file(model_path),
        "crossing_pattern_path": pattern_path.name,
        "crossing_pattern_sha256": sha256_file(pattern_path),
        "validation": validation,
    }
    total = manifest["partition"]["total_cubes"]
    atomic_write_json(
        cube_path(run_dir, cube_record["cube_index"], total), cube_record
    )
    return write_sat_final(run_dir, manifest, cube_record)


def write_sat_final(
    run_dir: Path,
    manifest: dict[str, Any],
    cube_record: dict[str, Any],
) -> dict[str, Any]:
    final = {
        "schema_version": SCHEMA_VERSION,
        "run_id": manifest["run_id"],
        "finished_utc": utc_now(),
        "result": "SAT",
        "formula_sha256": manifest["formula"]["sha256"],
        "partition_sha256": manifest["partition"]["sha256"],
        "sat_cube_index": cube_record["cube_index"],
        "solver": manifest["solver"],
        "sat_model": cube_record["sat_model"],
        "evidence": {
            "model_checked_against_encoded_formula": True,
            "encoder_fidelity_requires_separate_mathematical_audit": True,
        },
    }
    atomic_write_json(run_dir / "final-result.json", final)
    return final


def safe_artifact_path(run_dir: Path, name: str) -> Path:
    candidate = Path(name)
    if candidate.is_absolute() or candidate.name != name:
        raise RuntimeError(f"unsafe SAT artifact path {name!r}")
    return run_dir / candidate


def load_and_verify_sat_artifacts(
    run_dir: Path,
    manifest: dict[str, Any],
    cube_record: dict[str, Any],
    cnf,
    xor_clauses,
    crossing_vars: dict,
) -> dict[str, Any]:
    model_info = cube_record.get("sat_model")
    if not isinstance(model_info, dict):
        raise RuntimeError("SAT cube is missing its model metadata")
    model_path = safe_artifact_path(run_dir, model_info["path"])
    pattern_path = safe_artifact_path(run_dir, model_info["crossing_pattern_path"])
    if sha256_file(model_path) != model_info["sha256"]:
        raise RuntimeError("SAT model hash does not match")
    if sha256_file(pattern_path) != model_info["crossing_pattern_sha256"]:
        raise RuntimeError("SAT crossing pattern hash does not match")

    model_record = load_json(model_path)
    identity = {
        "schema_version": SCHEMA_VERSION,
        "run_id": manifest["run_id"],
        "formula_sha256": manifest["formula"]["sha256"],
        "partition_sha256": manifest["partition"]["sha256"],
        "variable_count": manifest["formula"]["variables"],
    }
    for key, expected in identity.items():
        if model_record.get(key) != expected:
            raise RuntimeError(f"SAT model identity mismatch in {key}")
    true_variables = model_record.get("true_variables")
    if not isinstance(true_variables, list):
        raise RuntimeError("SAT model true_variables is not a list")
    normalized_true = [int(variable) for variable in true_variables]
    if normalized_true != sorted(set(normalized_true)):
        raise RuntimeError("SAT model true_variables is not sorted and unique")
    variable_count = manifest["formula"]["variables"]
    if any(not 1 <= variable <= variable_count for variable in normalized_true):
        raise RuntimeError("SAT model contains an invalid variable")
    model = [False] * (variable_count + 1)
    for variable in normalized_true:
        model[variable] = True
    validation = verify_model(cnf, xor_clauses, model, cube_record["assumptions"])
    if model_record.get("validation") != validation:
        raise RuntimeError("SAT model's saved validation summary is inconsistent")
    if model_info.get("validation") != validation:
        raise RuntimeError("SAT cube's validation summary is inconsistent")

    pattern_record = load_json(pattern_path)
    expected_pattern = {
        "schema_version": SCHEMA_VERSION,
        "run_id": manifest["run_id"],
        "formula_sha256": manifest["formula"]["sha256"],
        "partition_sha256": manifest["partition"]["sha256"],
        **crossing_pattern(manifest["config"]["n"], crossing_vars, model),
    }
    if pattern_record != expected_pattern:
        raise RuntimeError("saved SAT crossing pattern does not match the Boolean model")
    return validation


def recover_sat_final(
    run_dir: Path,
    manifest: dict[str, Any],
    cube_record: dict[str, Any],
    cnf,
    xor_clauses,
    crossing_vars: dict,
) -> dict[str, Any]:
    """Finish the small crash window after the SAT cube was checkpointed."""
    load_and_verify_sat_artifacts(
        run_dir, manifest, cube_record, cnf, xor_clauses, crossing_vars
    )
    return write_sat_final(run_dir, manifest, cube_record)


def save_unsat_final(
    run_dir: Path,
    manifest: dict[str, Any],
    completed: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    total = manifest["partition"]["total_cubes"]
    if set(completed) != set(range(total)):
        raise RuntimeError("cannot finalize UNSAT before every cube is complete")
    if any(record["result"] != "UNSAT" for record in completed.values()):
        raise RuntimeError("cannot finalize UNSAT when a cube is not UNSAT")
    final = {
        "schema_version": SCHEMA_VERSION,
        "run_id": manifest["run_id"],
        "finished_utc": utc_now(),
        "result": "UNSAT",
        "formula_sha256": manifest["formula"]["sha256"],
        "partition_sha256": manifest["partition"]["sha256"],
        "partition_kind": manifest["partition"]["kind"],
        "solver": manifest["solver"],
        "completed_unsat_cubes": total,
        "total_cubes": total,
        "cube_files_aggregate_sha256": aggregate_cube_hash(run_dir, total),
        "total_recorded_solve_seconds": sum(
            float(record["solve_seconds"]) for record in completed.values()
        ),
        "evidence": {
            "kind": "reproducible-solver-audit",
            "verification_level": "UNCERTIFIED_SOLVER_AUDIT",
            "claim_scope": "HASHED_ENCODED_FORMULA_ONLY",
            "independently_checkable_unsat_proof": False,
            "encoder_fidelity_requires_separate_mathematical_audit": True,
            "human_summary": (
                "For this exact hashed encoded formula, pycryptosat reported every "
                "exhaustive cube UNSAT. This is a reproducible computation record, "
                "not an independently checkable proof certificate."
            ),
            "warning": (
                "All exhaustive cubes were reported UNSAT by CryptoMiniSat, but the "
                "native-XOR binding did not emit a proof certificate."
            ),
        },
    }
    atomic_write_json(run_dir / "final-result.json", final)
    return final


def request_safe_stop(run_dir: Path) -> int:
    if (run_dir / "final-result.json").exists():
        print("The run is already complete; no stop request was created.", flush=True)
        return 0
    if not (run_dir / "manifest.json").exists():
        print(f"No initialized run exists in {run_dir}; nothing to stop.", flush=True)
        return 1
    request_path = run_dir / STOP_REQUEST_NAME
    if request_path.exists():
        request = load_json(request_path)
        print(
            f"A safe-stop request already exists (created {request.get('created_utc')}).",
            flush=True,
        )
        return 0
    atomic_write_json(
        request_path,
        {
            "schema_version": SCHEMA_VERSION,
            "kind": "stop-after-current-cube",
            "created_utc": utc_now(),
            "requesting_pid": os.getpid(),
            "requesting_hostname": socket.gethostname(),
        },
    )
    print(
        "Safe stop requested. The runner will stop after the active cube is "
        "checkpointed; if it is between cubes, it will stop before starting another.",
        flush=True,
    )
    return 0


def consume_safe_stop_request(run_dir: Path) -> dict[str, Any] | None:
    request_path = run_dir / STOP_REQUEST_NAME
    if not request_path.exists():
        return None
    request = load_json(request_path)
    if not isinstance(request, dict) or request.get("kind") != "stop-after-current-cube":
        raise RuntimeError("invalid safe-stop request; refusing to continue")
    archive_dir = run_dir / "stop-requests"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / (
        f"acknowledged-{safe_timestamp()}-{uuid.uuid4().hex[:8]}.json"
    )
    os.replace(request_path, archive_path)
    request["acknowledged_utc"] = utc_now()
    request["acknowledged_by_pid"] = os.getpid()
    atomic_write_json(archive_path, request)
    return request


def print_status(run_dir: Path) -> int:
    final_path = run_dir / "final-result.json"
    status_path = run_dir / "status.json"
    manifest_path = run_dir / "manifest.json"
    if final_path.exists():
        print(json.dumps(load_json(final_path), ensure_ascii=False, indent=2))
        return 0
    if status_path.exists():
        status = load_json(status_path)
        pid = int(status.get("pid", -1))
        status["process_alive_now"] = process_is_alive(pid)
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 0
    if manifest_path.exists():
        manifest = load_json(manifest_path)
        print(
            json.dumps(
                {
                    "state": "MANIFEST_ONLY",
                    "run_id": manifest.get("run_id"),
                    "total_cubes": manifest.get("partition", {}).get("total_cubes"),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    print(f"No run found in {run_dir}")
    return 1


def verify_existing_run(
    run_dir: Path,
    manifest: dict[str, Any],
    completed: dict[int, dict[str, Any]],
    cnf,
    xor_clauses,
    crossing_vars: dict,
) -> None:
    final_path = run_dir / "final-result.json"
    if not final_path.exists():
        print(
            f"AUDIT partial: {len(completed)}/{manifest['partition']['total_cubes']} "
            "cube checkpoints are structurally valid",
            flush=True,
        )
        return
    final = load_json(final_path)
    if final.get("run_id") != manifest["run_id"]:
        raise RuntimeError("final result has the wrong run ID")
    if final.get("formula_sha256") != manifest["formula"]["sha256"]:
        raise RuntimeError("final result has the wrong formula hash")
    if final.get("partition_sha256") != manifest["partition"]["sha256"]:
        raise RuntimeError("final result has the wrong partition hash")
    if final.get("result") == "UNSAT":
        total = manifest["partition"]["total_cubes"]
        if set(completed) != set(range(total)):
            raise RuntimeError("UNSAT final is missing cube checkpoints")
        if any(record.get("result") != "UNSAT" for record in completed.values()):
            raise RuntimeError("UNSAT final contains a non-UNSAT cube")
        if final.get("completed_unsat_cubes") != total or final.get("total_cubes") != total:
            raise RuntimeError("UNSAT final has incorrect cube counts")
        evidence = final.get("evidence", {})
        if evidence.get("verification_level") != "UNCERTIFIED_SOLVER_AUDIT":
            raise RuntimeError("UNSAT final has an incorrect verification level")
        if evidence.get("independently_checkable_unsat_proof") is not False:
            raise RuntimeError("UNSAT final incorrectly claims an independent certificate")
        expected_hash = aggregate_cube_hash(run_dir, total)
        if final.get("cube_files_aggregate_sha256") != expected_hash:
            raise RuntimeError("UNSAT cube aggregate hash does not match")
        print(
            f"AUDIT-ONLY solver-reported UNSAT record: all {total} cube files "
            "and hashes are intact; no independent proof certificate exists",
            flush=True,
        )
        return
    if final.get("result") == "SAT":
        cube_index = int(final["sat_cube_index"])
        cube_record = completed.get(cube_index)
        if cube_record is None or cube_record.get("result") != "SAT":
            raise RuntimeError("SAT final is missing its SAT cube checkpoint")
        if final.get("sat_model") != cube_record.get("sat_model"):
            raise RuntimeError("SAT final and cube disagree about model artifacts")
        load_and_verify_sat_artifacts(
            run_dir, manifest, cube_record, cnf, xor_clauses, crossing_vars
        )
        print("AUDIT SAT record: model satisfies the encoded CNF and XOR formula", flush=True)
        return
    raise RuntimeError("final result is neither SAT nor UNSAT")


def run_cubes(
    args,
    run_dir: Path,
    manifest: dict[str, Any],
    completed: dict[int, dict[str, Any]],
    cnf,
    xor_clauses,
    crossing_vars: dict,
    status: StatusWriter,
) -> int:
    final_path = run_dir / "final-result.json"
    if final_path.exists():
        verify_existing_run(
            run_dir, manifest, completed, cnf, xor_clauses, crossing_vars
        )
        print(json.dumps(load_json(final_path), ensure_ascii=False, indent=2), flush=True)
        status.update(state="COMPLETE", current_cube=None)
        return 0

    total = manifest["partition"]["total_cubes"]
    groups = manifest["partition"]["groups"]
    sat_records = [record for record in completed.values() if record["result"] == "SAT"]
    if len(sat_records) > 1:
        raise RuntimeError("more than one SAT cube checkpoint exists")
    if sat_records:
        final = recover_sat_final(
            run_dir,
            manifest,
            sat_records[0],
            cnf,
            xor_clauses,
            crossing_vars,
        )
        status.update(
            state="COMPLETE",
            result="SAT",
            current_cube=None,
            completed_cubes=len(completed),
            message="Recovered and verified a SAT result after an interrupted final write.",
        )
        print(json.dumps(final, ensure_ascii=False, indent=2), flush=True)
        return 10

    if len(completed) == total:
        final = save_unsat_final(run_dir, manifest, completed)
        consume_safe_stop_request(run_dir)
        status.update(
            state="COMPLETE",
            result="UNSAT",
            current_cube=None,
            completed_cubes=total,
            total_cubes=total,
            message="Recovered the final UNSAT summary from complete cube records.",
        )
        print(json.dumps(final, ensure_ascii=False, indent=2), flush=True)
        return 20

    stop_request = consume_safe_stop_request(run_dir)
    if stop_request is not None:
        status.update(
            state="PAUSED_BY_REQUEST",
            current_cube=None,
            message="Safe-stop request acknowledged before starting a new cube.",
        )
        print("safe-stop request acknowledged; no new cube was started", flush=True)
        return 0

    print(
        f"resume state: {len(completed)}/{total} cubes complete; building solver",
        flush=True,
    )
    solver = pycryptosat.Solver(threads=args.threads)
    solver.add_clauses(cnf.clauses)
    for variables, rhs in xor_clauses:
        solver.add_xor_clause(variables, rhs)

    session_id = uuid.uuid4().hex
    newly_completed = 0
    for index in range(total):
        if index in completed:
            continue
        digits, assumptions = cube_assumptions(groups, index)
        started_utc = utc_now()
        status.update(
            state="SOLVING",
            current_cube=index,
            current_cube_choices=digits,
            current_cube_started_utc=started_utc,
            completed_cubes=len(completed),
            total_cubes=total,
        )
        started = time.perf_counter()
        satisfiable, solution = solver.solve(assumptions=assumptions)
        solve_seconds = time.perf_counter() - started
        result = "UNKNOWN" if satisfiable is None else ("SAT" if satisfiable else "UNSAT")
        record = {
            "schema_version": SCHEMA_VERSION,
            "run_id": manifest["run_id"],
            "formula_sha256": manifest["formula"]["sha256"],
            "partition_sha256": manifest["partition"]["sha256"],
            "cube_index": index,
            "choices": digits,
            "assumptions": assumptions,
            "assumption_semantics": cube_semantics(groups, digits),
            "started_utc": started_utc,
            "finished_utc": utc_now(),
            "solve_seconds": solve_seconds,
            "result": result,
            "solver": manifest["solver"],
            "session_id": session_id,
            "pid": os.getpid(),
            "hostname": socket.gethostname(),
        }
        if satisfiable is None:
            attempts = run_dir / "unknown-attempts"
            atomic_write_json(
                attempts / f"cube-{index:06d}-{safe_timestamp()}.json", record
            )
            status.update(
                state="PAUSED_UNKNOWN",
                current_cube=None,
                message="solver returned UNKNOWN; this cube was not marked complete",
            )
            print(f"cube {index}/{total - 1}: UNKNOWN after {solve_seconds:.3f}s", flush=True)
            return 3
        if satisfiable:
            final = save_sat_result(
                run_dir,
                manifest,
                record,
                solution,
                cnf,
                xor_clauses,
                crossing_vars,
            )
            consume_safe_stop_request(run_dir)
            completed[index] = record
            status.update(
                state="COMPLETE",
                result="SAT",
                current_cube=None,
                completed_cubes=len(completed),
            )
            print(json.dumps(final, ensure_ascii=False, indent=2), flush=True)
            return 10

        raw_conflict = solver.get_conflict()
        conflict_clause = [] if raw_conflict is None else [
            int(literal) for literal in raw_conflict
        ]
        if not all(-literal in assumptions for literal in conflict_clause):
            raise RuntimeError(
                f"solver returned a malformed blocking clause for cube {index}"
            )
        record["diagnostic_conflict"] = {
            "solver_reported_blocking_clause": conflict_clause,
            "solver_reported_assumption_core": [-literal for literal in conflict_clause],
            "structurally_consistent_with_assumptions": True,
            "independently_verified": False,
            "is_proof_certificate": False,
            "note": (
                "This solver diagnostic is the negation of an assumption core; "
                "it is not an independently checkable UNSAT proof."
            ),
        }
        atomic_write_json(cube_path(run_dir, index, total), record)
        completed[index] = record
        newly_completed += 1
        print(
            f"cube {index + 1}/{total}: UNSAT in {solve_seconds:.3f}s "
            f"({len(completed)} complete)",
            flush=True,
        )
        status.update(
            state="BETWEEN_CUBES",
            current_cube=None,
            last_completed_cube=index,
            completed_cubes=len(completed),
            total_cubes=total,
        )
        if len(completed) < total and consume_safe_stop_request(run_dir) is not None:
            status.update(
                state="PAUSED_BY_REQUEST",
                current_cube=None,
                message="Safe-stop request acknowledged after checkpointing the cube.",
            )
            print(
                "safe-stop request acknowledged after the completed cube was saved; "
                "rerun the same command to resume",
                flush=True,
            )
            return 0
        if args.max_new_cubes is not None and newly_completed >= args.max_new_cubes:
            status.update(
                state="PAUSED_BY_REQUEST",
                message=f"stopped after {newly_completed} new cubes",
            )
            print("paused by --max-new-cubes; rerun the same command to resume", flush=True)
            return 0

    final = save_unsat_final(run_dir, manifest, completed)
    consume_safe_stop_request(run_dir)
    status.update(
        state="COMPLETE",
        result="UNSAT",
        current_cube=None,
        completed_cubes=total,
        total_cubes=total,
    )
    print(json.dumps(final, ensure_ascii=False, indent=2), flush=True)
    return 20


def parse_args():
    parser = argparse.ArgumentParser(
        description="Crash-resumable exhaustive cube runner for the crossing parity model"
    )
    parser.add_argument("n", type=int)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--induction-witness", action="store_true")
    parser.add_argument("--all-deletion-witnesses", action="store_true")
    parser.add_argument("--k5-encoding", choices=("nogoods", "mdd"), default="nogoods")
    parser.add_argument(
        "--parity-encoding",
        choices=("direct",),
        default="direct",
        help="the checkpoint partition audit currently supports direct encoding only",
    )
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--cube-depth", type=int, default=6)
    parser.add_argument("--heartbeat-seconds", type=float, default=30.0)
    parser.add_argument("--max-new-cubes", type=int)
    parser.add_argument("--status-only", action="store_true")
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument(
        "--request-stop",
        action="store_true",
        help="ask an active run to stop safely after its current cube",
    )
    args = parser.parse_args()
    if args.n < 4:
        parser.error("n must be at least 4")
    if args.threads < 1:
        parser.error("threads must be positive")
    if args.max_new_cubes is not None and args.max_new_cubes < 1:
        parser.error("--max-new-cubes must be positive")
    if args.heartbeat_seconds < 0:
        parser.error("--heartbeat-seconds cannot be negative")
    return args


def main() -> int:
    args = parse_args()
    run_dir = args.run_dir.resolve()
    if args.status_only:
        return print_status(run_dir)
    if args.request_stop:
        return request_safe_stop(run_dir)

    run_dir.mkdir(parents=True, exist_ok=True)
    lock = RunLock(run_dir)
    status: StatusWriter | None = None
    try:
        lock.acquire()
        moved_temps = quarantine_orphan_temp_files(run_dir)
        if moved_temps:
            print(
                f"preserved {len(moved_temps)} incomplete atomic-write file(s) "
                "under orphaned-temp",
                flush=True,
            )
        config = runner_config(args)
        print("building encoded instance", config, flush=True)
        cnf, xor_clauses, stats, metadata = build_instance(
            args.n,
            args.induction_witness,
            args.all_deletion_witnesses,
            native_xor=True,
            k5_encoding=args.k5_encoding,
            parity_encoding=args.parity_encoding,
            return_metadata=True,
        )
        counts = formula_counts(stats)
        formula_hash = formula_sha256(cnf, xor_clauses)
        files = current_file_inventory()
        manifest = load_or_create_manifest(
            run_dir,
            config,
            counts,
            formula_hash,
            files,
            metadata["crossing_vars"],
            cnf,
        )
        completed = load_completed_cubes(run_dir, manifest)
        status = StatusWriter(
            run_dir / "status.json",
            args.heartbeat_seconds,
            {
                "schema_version": SCHEMA_VERSION,
                "run_id": manifest["run_id"],
                "pid": os.getpid(),
                "hostname": socket.gethostname(),
                "state": "READY",
                "formula_sha256": formula_hash,
                "completed_cubes": len(completed),
                "total_cubes": manifest["partition"]["total_cubes"],
                "current_cube": None,
            },
        )
        status.start()
        print(
            "formula",
            {**counts, "sha256": formula_hash},
            "checkpoint",
            str(run_dir),
            flush=True,
        )
        if args.audit_only:
            verify_existing_run(
                run_dir,
                manifest,
                completed,
                cnf,
                xor_clauses,
                metadata["crossing_vars"],
            )
            status.update(state="AUDITED", current_cube=None)
            return 0
        return run_cubes(
            args,
            run_dir,
            manifest,
            completed,
            cnf,
            xor_clauses,
            metadata["crossing_vars"],
            status,
        )
    except KeyboardInterrupt:
        if status is not None:
            status.update(
                state="INTERRUPTED",
                current_cube=None,
                message="The active cube was not checkpointed; completed cubes are safe.",
            )
        print(
            "interrupted: completed cubes are preserved; rerun the same command to resume",
            file=sys.stderr,
            flush=True,
        )
        return 130
    except Exception as exc:
        error = {
            "schema_version": SCHEMA_VERSION,
            "time_utc": utc_now(),
            "pid": os.getpid(),
            "error_type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
        try:
            atomic_write_json(run_dir / "last-error.json", error)
            errors_dir = run_dir / "errors"
            atomic_write_json(
                errors_dir / f"error-{safe_timestamp()}-{uuid.uuid4().hex[:8]}.json",
                error,
            )
            if status is not None:
                status.update(state="ERROR", current_cube=None, message=str(exc))
        finally:
            print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        return 1
    finally:
        if status is not None:
            status.stop()
        lock.release()


if __name__ == "__main__":
    raise SystemExit(main())
