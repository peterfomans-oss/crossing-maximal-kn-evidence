"""Construct sparse generators for crossing-maximal parity patterns.

A generator is the sum of two edge-vertex switches supported on one triangle,
so it toggles two crossing choices in every K4 containing that triangle and
therefore preserves the odd-K4 condition.
"""

from __future__ import annotations

import itertools
import sys


def normalized_pair(edge1, edge2):
    return tuple(sorted((tuple(sorted(edge1)), tuple(sorted(edge2)))))


def matching_edges(vertices):
    a, b, c, d = vertices
    return (((a, b), (c, d)), ((a, c), (b, d)), ((a, d), (b, c)))


def crossing_columns(n: int):
    columns = {}
    for quad in itertools.combinations(range(n), 4):
        for pair in matching_edges(quad):
            columns[normalized_pair(*pair)] = len(columns)
    return columns


def switch_vector(n: int, columns, edge, vertex):
    edge = tuple(sorted(edge))
    result = 0
    for other in range(n):
        if other == vertex or other in edge:
            continue
        pair = normalized_pair(edge, (vertex, other))
        result ^= 1 << columns[pair]
    return result


def triangle_generators(n: int, columns):
    generators = []
    for a, b, c in itertools.combinations(range(n), 3):
        anchor = switch_vector(n, columns, (a, b), c)
        generators.append(((a, b, c, 0), anchor ^ switch_vector(n, columns, (a, c), b)))
        generators.append(((a, b, c, 1), anchor ^ switch_vector(n, columns, (b, c), a)))
    return generators


def independent_subset(generators):
    basis_by_pivot = {}
    selected = []
    for name, original in generators:
        reduced = original
        while reduced:
            pivot = reduced.bit_length() - 1
            if pivot not in basis_by_pivot:
                basis_by_pivot[pivot] = reduced
                selected.append((name, original))
                break
            reduced ^= basis_by_pivot[pivot]
    return selected


def main():
    upper = int(sys.argv[1]) if len(sys.argv) > 1 else 17
    for n in range(4, upper + 1):
        columns = crossing_columns(n)
        generators = triangle_generators(n, columns)
        selected = independent_subset(generators)
        coordinate_widths = [0] * len(columns)
        for _, vector in selected:
            while vector:
                bit = vector & -vector
                coordinate_widths[bit.bit_length() - 1] += 1
                vector ^= bit
        expected = n * (n - 1) * (2 * n - 7) // 6
        print(
            f"n={n} candidates={len(generators)} rank={len(selected)} expected={expected} "
            f"max_coordinate_width={max(coordinate_widths)} "
            f"avg_coordinate_width={sum(coordinate_widths)/len(coordinate_widths):.3f}"
        )


if __name__ == "__main__":
    main()
