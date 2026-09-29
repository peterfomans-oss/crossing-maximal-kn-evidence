"""Explore a crossing-only local model for crossing-maximal drawings.

Each 4-set receives one of its three perfect matchings as the crossing pair.
The script extracts labelled local pattern dictionaries from the upstream
rotation-system enumeration and compares 5-local consistency with the exact
6-vertex dictionary.
"""

from __future__ import annotations

import ast
import itertools
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def read_rotation_systems(path: Path) -> list[list[list[int]]]:
    return [ast.literal_eval(line) for line in path.read_text().splitlines() if line.strip()]


def cyclic_order(rotation: list[int], b: int, c: int, d: int) -> bool:
    """Return whether b,c,d occur in this cyclic order in ``rotation``."""
    pos = {value: index for index, value in enumerate(rotation)}
    size = len(rotation)
    return (pos[c] - pos[b]) % size < (pos[d] - pos[b]) % size


def directed_crossing(rs: list[list[int]], a: int, b: int, c: int, d: int) -> bool:
    """Mirror the D_abcd definition in rotsys.py."""
    return (
        cyclic_order(rs[a], b, d, c)
        and cyclic_order(rs[b], a, c, d)
        and cyclic_order(rs[c], a, b, d)
        and cyclic_order(rs[d], a, c, b)
    )


def crossing(rs: list[list[int]], edge1: tuple[int, int], edge2: tuple[int, int]) -> bool:
    a, b = edge1
    c, d = edge2
    return directed_crossing(rs, a, b, c, d) or directed_crossing(rs, a, b, d, c)


def matching_edges(vertices: tuple[int, int, int, int]) -> tuple[tuple[tuple[int, int], tuple[int, int]], ...]:
    a, b, c, d = vertices
    return (((a, b), (c, d)), ((a, c), (b, d)), ((a, d), (b, c)))


def pattern_from_rotation(rs: list[list[int]]) -> tuple[int, ...]:
    pattern: list[int] = []
    for quad in itertools.combinations(range(len(rs)), 4):
        hits = [i for i, pair in enumerate(matching_edges(quad)) if crossing(rs, *pair)]
        if len(hits) != 1:
            raise ValueError(f"expected exactly one crossing on {quad}, got {hits}")
        pattern.append(hits[0])
    return tuple(pattern)


def oriented_state_pattern(rs: list[list[int]]) -> tuple[int, ...]:
    """Encode each K4 by crossing choice (0..2) and one mirror bit (0..1)."""
    crossing_pattern = pattern_from_rotation(rs)
    result = []
    for quad, choice in zip(
        itertools.combinations(range(len(rs)), 4), crossing_pattern, strict=True
    ):
        a, b, c, d = quad
        mirror_bit = int(cyclic_order(rs[a], b, c, d))
        result.append(2 * choice + mirror_bit)
    return tuple(result)


def crossing_pairs_from_pattern(n: int, pattern: tuple[int, ...]):
    pairs = set()
    for quad, choice in zip(itertools.combinations(range(n), 4), pattern, strict=True):
        edge1, edge2 = matching_edges(quad)[choice]
        pairs.add((tuple(sorted(edge1)), tuple(sorted(edge2))))
    return pairs


def normalized_pair(edge1: tuple[int, int], edge2: tuple[int, int]):
    e1, e2 = tuple(sorted(edge1)), tuple(sorted(edge2))
    return tuple(sorted((e1, e2)))


def relabel_pattern(n: int, pattern: tuple[int, ...], permutation: tuple[int, ...]) -> tuple[int, ...]:
    mapped_pairs = {
        normalized_pair(tuple(permutation[v] for v in e1), tuple(permutation[v] for v in e2))
        for e1, e2 in crossing_pairs_from_pattern(n, pattern)
    }
    result = []
    for quad in itertools.combinations(range(n), 4):
        choices = [normalized_pair(*pair) for pair in matching_edges(quad)]
        hits = [i for i, pair in enumerate(choices) if pair in mapped_pairs]
        if len(hits) != 1:
            raise ValueError((quad, hits))
        result.append(hits[0])
    return tuple(result)


def labelled_orbit(n: int, patterns: list[tuple[int, ...]]) -> set[tuple[int, ...]]:
    result = set()
    for permutation in itertools.permutations(range(n)):
        for pattern in patterns:
            result.add(relabel_pattern(n, pattern, permutation))
    return result


def relabel_rotation(rs: list[list[int]], permutation: tuple[int, ...], mirror: bool):
    inverse = {permutation[old]: old for old in range(len(permutation))}
    result = []
    for new_vertex in range(len(permutation)):
        old_vertex = inverse[new_vertex]
        row = [permutation[value] for value in rs[old_vertex]]
        if mirror:
            row = list(reversed(row))
        result.append(row)
    return result


def labelled_oriented_states(rotation_systems: list[list[list[int]]]):
    n = len(rotation_systems[0])
    result = set()
    for permutation in itertools.permutations(range(n)):
        for rs in rotation_systems:
            for mirror in (False, True):
                result.add(oriented_state_pattern(relabel_rotation(rs, permutation, mirror)))
    return result


def reduced_mdd_size(patterns: set[tuple[int, ...]], order: tuple[int, ...]):
    """Return reduced ordered multi-valued decision diagram node counts by level."""
    reordered = [tuple(pattern[i] for i in order) for pattern in patterns]
    child_ids = {pattern: 1 for pattern in reordered}
    counts_reversed = []
    for depth in range(len(order) - 1, -1, -1):
        prefixes = {pattern[:depth] for pattern in reordered}
        signatures = {}
        for prefix in prefixes:
            transitions = []
            values = sorted({pattern[depth] for pattern in reordered if pattern[:depth] == prefix})
            for value in values:
                transitions.append((value, child_ids[prefix + (value,)]))
            signatures[prefix] = tuple(transitions)
        unique_signatures = {signature: i + 1 for i, signature in enumerate(sorted(set(signatures.values())))}
        child_ids = {
            prefix: unique_signatures[signature] for prefix, signature in signatures.items()
        }
        counts_reversed.append(len(unique_signatures))
    return tuple(reversed(counts_reversed))


def restrict_pattern(
    n: int, pattern: tuple[int, ...], subset: tuple[int, ...]
) -> tuple[int, ...]:
    choice_by_quad = dict(zip(itertools.combinations(range(n), 4), pattern, strict=True))
    index = {vertex: i for i, vertex in enumerate(subset)}
    restricted_pairs = set()
    for quad in itertools.combinations(subset, 4):
        pair = matching_edges(quad)[choice_by_quad[quad]]
        restricted_pairs.add(
            normalized_pair(
                tuple(index[v] for v in pair[0]),
                tuple(index[v] for v in pair[1]),
            )
        )
    result = []
    for quad in itertools.combinations(range(len(subset)), 4):
        options = [normalized_pair(*pair) for pair in matching_edges(quad)]
        result.append(next(i for i, option in enumerate(options) if option in restricted_pairs))
    return tuple(result)


def enumerate_five_local_k6(allowed5: set[tuple[int, ...]]) -> set[tuple[int, ...]]:
    """Backtrack through 15 K4 choices, pruning complete K5 restrictions."""
    quads = list(itertools.combinations(range(6), 4))
    fives = list(itertools.combinations(range(6), 5))
    quad_index = {quad: i for i, quad in enumerate(quads)}
    five_quad_indices = [
        [quad_index[q] for q in itertools.combinations(five, 4)] for five in fives
    ]
    allowed5_lists = [set(allowed5) for _ in fives]
    result: set[tuple[int, ...]] = set()
    partial = [-1] * len(quads)

    def visit(position: int) -> None:
        if position == len(quads):
            result.add(tuple(partial))
            return
        for value in range(3):
            partial[position] = value
            valid = True
            for indices, allowed in zip(five_quad_indices, allowed5_lists, strict=True):
                if all(partial[i] >= 0 for i in indices):
                    local = tuple(partial[i] for i in indices)
                    if local not in allowed:
                        valid = False
                        break
            if valid:
                visit(position + 1)
        partial[position] = -1

    visit(0)
    return result


def even_disjoint_triangles(pattern: tuple[int, ...]) -> bool:
    """Test Kyncl's even-2K3 condition for a crossing pattern on K6."""
    pairs = crossing_pairs_from_pattern(6, pattern)
    vertices = set(range(6))
    seen_partitions = set()
    for first in itertools.combinations(range(6), 3):
        second = tuple(sorted(vertices - set(first)))
        partition = tuple(sorted((tuple(first), second)))
        if partition in seen_partitions:
            continue
        seen_partitions.add(partition)
        first_edges = list(itertools.combinations(partition[0], 2))
        second_edges = list(itertools.combinations(partition[1], 2))
        count = sum(
            normalized_pair(e1, e2) in pairs for e1 in first_edges for e2 in second_edges
        )
        if count % 2:
            return False
    return True


def main() -> None:
    cm5 = [pattern_from_rotation(rs) for rs in read_rotation_systems(ROOT / "cm5_unlabeled.json0")]
    cm6 = [pattern_from_rotation(rs) for rs in read_rotation_systems(ROOT / "cm6_unlabeled.json0")]
    labelled5 = labelled_orbit(5, cm5)
    labelled6 = labelled_orbit(6, cm6)
    five_local6 = enumerate_five_local_k6(labelled5)

    print(f"unlabelled K5 types: {len(set(cm5))}")
    print(f"labelled K5 patterns: {len(labelled5)}")
    print(f"unlabelled K6 types: {len(set(cm6))}")
    print(f"labelled K6 patterns: {len(labelled6)}")
    print(f"K6 patterns passing every K5 table: {len(five_local6)}")
    print(f"five-local false positives: {len(five_local6 - labelled6)}")
    print(f"exact K6 patterns rejected by five-local test: {len(labelled6 - five_local6)}")

    # Independent sanity check: all K5 restrictions of exact K6 patterns are allowed.
    bad_restrictions = []
    for pattern in labelled6:
        for subset in itertools.combinations(range(6), 5):
            if restrict_pattern(6, pattern, subset) not in labelled5:
                bad_restrictions.append((pattern, subset))
    print(f"bad exact K6 -> K5 restrictions: {len(bad_restrictions)}")
    parity6 = {pattern for pattern in five_local6 if even_disjoint_triangles(pattern)}
    print(f"five-local K6 patterns also passing every even-2K3 test: {len(parity6)}")
    print(f"parity-stage false positives: {len(parity6 - labelled6)}")
    print(f"exact K6 patterns rejected by parity: {len(labelled6 - parity6)}")

    labelled5_by_type = [labelled_orbit(5, [pattern]) for pattern in cm5]

    def type_vector(pattern: tuple[int, ...]) -> tuple[int, ...]:
        result = []
        for subset in itertools.combinations(range(6), 5):
            local = restrict_pattern(6, pattern, subset)
            memberships = [i for i, orbit in enumerate(labelled5_by_type) if local in orbit]
            if len(memberships) != 1:
                raise ValueError((local, memberships))
            result.append(memberships[0])
        return tuple(result)

    exact_type_vectors: dict[tuple[int, ...], int] = {}
    false_type_vectors: dict[tuple[int, ...], int] = {}
    for pattern in labelled6:
        vector = type_vector(pattern)
        exact_type_vectors[vector] = exact_type_vectors.get(vector, 0) + 1
    for pattern in five_local6 - labelled6:
        vector = type_vector(pattern)
        false_type_vectors[vector] = false_type_vectors.get(vector, 0) + 1

    print("exact K5-type vector distribution:")
    for vector, count in sorted(exact_type_vectors.items()):
        print("  ", "".join(map(str, vector)), count)
    print("false-positive K5-type vector distribution:")
    for vector, count in sorted(false_type_vectors.items()):
        print("  ", "".join(map(str, vector)), count)

    oriented5 = labelled_oriented_states(read_rotation_systems(ROOT / "cm5_unlabeled.json0"))
    print(f"labelled oriented K5 state patterns: {len(oriented5)}")
    for type_index, pattern in enumerate(cm5):
        degrees = {edge: 0 for edge in itertools.combinations(range(5), 2)}
        for e1, e2 in crossing_pairs_from_pattern(5, pattern):
            degrees[e1] += 1
            degrees[e2] += 1
        print(
            f"K5 type {type_index}: choices={pattern}, "
            f"crossing-degree multiset={sorted(degrees.values())}"
        )
    allowed_degree_multisets = set()
    for pattern in cm5:
        degrees = {edge: 0 for edge in itertools.combinations(range(5), 2)}
        for e1, e2 in crossing_pairs_from_pattern(5, pattern):
            degrees[e1] += 1
            degrees[e2] += 1
        allowed_degree_multisets.add(tuple(sorted(degrees.values())))
    degree_characterized = set()
    for candidate in itertools.product(range(3), repeat=5):
        degrees = {edge: 0 for edge in itertools.combinations(range(5), 2)}
        for e1, e2 in crossing_pairs_from_pattern(5, candidate):
            degrees[e1] += 1
            degrees[e2] += 1
        if tuple(sorted(degrees.values())) in allowed_degree_multisets:
            degree_characterized.add(candidate)
    print(
        f"K5 patterns accepted by the two degree multisets: {len(degree_characterized)}; "
        f"false positives={len(degree_characterized - labelled5)}"
    )
    crossing_mdd_results = []
    for order in itertools.permutations(range(5)):
        counts = reduced_mdd_size(labelled5, order)
        crossing_mdd_results.append((sum(counts), counts, order))
    for total, counts, order in sorted(crossing_mdd_results)[:3]:
        print(f"crossing-only K5 MDD order={order}, levels={counts}, total={total}")
    for arity in range(1, 6):
        position_sets = list(itertools.combinations(range(5), arity))
        projections = {
            positions: {tuple(pattern[i] for i in positions) for pattern in labelled5}
            for positions in position_sets
        }
        accepted = {
            candidate
            for candidate in itertools.product(range(3), repeat=5)
            if all(
                tuple(candidate[i] for i in positions) in projections[positions]
                for positions in position_sets
            )
        }
        forbidden_projection_tuples = sum(
            3**arity - len(projections[positions]) for positions in position_sets
        )
        print(
            f"crossing arity-{arity} closure: {len(accepted)} patterns; "
            f"forbidden local tuples={forbidden_projection_tuples}"
        )
    triple_forbidden = set()
    for positions in itertools.combinations(range(5), 3):
        allowed_projection = {tuple(pattern[i] for i in positions) for pattern in labelled5}
        for values in itertools.product(range(3), repeat=3):
            if values not in allowed_projection:
                triple_forbidden.add(tuple(zip(positions, values)))
    minimal_four_forbidden = set()
    for positions in itertools.combinations(range(5), 4):
        allowed_projection = {tuple(pattern[i] for i in positions) for pattern in labelled5}
        for values in itertools.product(range(3), repeat=4):
            if values in allowed_projection:
                continue
            assignment = dict(zip(positions, values))
            contains_bad_triple = any(
                tuple((position, assignment[position]) for position in triple_positions)
                in triple_forbidden
                for triple_positions in itertools.combinations(positions, 3)
            )
            if not contains_bad_triple:
                minimal_four_forbidden.add(tuple(zip(positions, values)))
    print(
        f"minimal crossing K5 nogoods: arity3={len(triple_forbidden)}, "
        f"arity4={len(minimal_four_forbidden)}, total={len(triple_forbidden)+len(minimal_four_forbidden)}"
    )
    mdd_results = []
    for order in itertools.permutations(range(5)):
        counts = reduced_mdd_size(oriented5, order)
        mdd_results.append((sum(counts), counts, order))
    for total, counts, order in sorted(mdd_results)[:5]:
        print(f"oriented K5 MDD order={order}, levels={counts}, total={total}")

    for arity in range(1, 6):
        position_sets = list(itertools.combinations(range(5), arity))
        projections = {
            positions: {tuple(pattern[i] for i in positions) for pattern in oriented5}
            for positions in position_sets
        }
        accepted = {
            candidate
            for candidate in itertools.product(range(6), repeat=5)
            if all(
                tuple(candidate[i] for i in positions) in projections[positions]
                for positions in position_sets
            )
        }
        forbidden_projection_tuples = sum(
            6**arity - len(projections[positions]) for positions in position_sets
        )
        print(
            f"arity-{arity} projection closure: {len(accepted)} patterns; "
            f"forbidden local tuples={forbidden_projection_tuples}"
        )


if __name__ == "__main__":
    main()
