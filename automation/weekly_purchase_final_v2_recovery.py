#!/usr/bin/env python3
"""Bounded exhaustive recovery runner for weekly purchase V2.

Keeps the same V2 joint five-ticket objective, but limits each of the six
predeclared signal families to its top 3 candidates. This yields at most 18
unique candidates and exhaustively evaluates every 5-ticket combination from
that pool at every walk-forward target, rather than using a greedy shortcut.
"""
import weekly_purchase_final_v2 as m

m.CANDIDATES_PER_FAMILY = 3
m.BACKTEST_TARGETS = 200
m.RANDOM_BUNDLES_PER_TARGET = 100
m.POLICY = "WEEKLY_FIVE_TICKET_PORTFOLIO_V2_PROTOCOL_FULL_R1"
_orig = m.candidate_bank
m.candidate_bank = lambda score, limit=3: _orig(score, 3)

if __name__ == "__main__":
    m.main()
