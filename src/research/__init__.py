"""Research layer — quantitative research, factors, backtests, and analysis.

Knowledge base for reusable research artifacts.

Modules:
    fgi/              Fear & Greed Index — 8-indicator A-share sentiment
    northbound/       北向资金 Smart Money — IC, streak, resonance
    limit_arb/        涨跌停统计套利 — board types, time effect, sector contagion
    sector_rotation/  行业轮动 — momentum + crowding dual factor

Usage:
    from src.research.fgi.engine import compute_fgi
    fgi = compute_fgi()

    from src.research.northbound.smart_money import run
    df = run()
"""
