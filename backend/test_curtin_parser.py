#!/usr/bin/env python3
"""
Quick test script for the Curtin outline parser.

Usage:
    cd backend
    python test_curtin_parser.py [path_to_pdf]

If no path is given, uses the fixture PDF.
"""

import asyncio
import sys
from pathlib import Path


async def main():
    from app.services.outline_parsers.curtin_parser import CurtinOutlineParser

    # Determine PDF path
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
    else:
        pdf_path = Path(__file__).parent.parent / "e2e" / "fixtures" / "ISYS6020-Artificial-Intelligence-in-Business-Strategy-and-Management.pdf"

    if not pdf_path.exists():
        print(f"ERROR: File not found: {pdf_path}")
        sys.exit(1)

    print(f"Parsing: {pdf_path.name}")
    print("=" * 70)

    content = pdf_path.read_bytes()
    parser = CurtinOutlineParser()
    result = await parser.parse(content, pdf_path.name, "pdf")

    # --- Metadata ---
    print("\n## METADATA")
    print(f"  Code:          {result.unit_code}")
    print(f"  Title:         {result.unit_title}")
    print(f"  Credits:       {result.credit_points}")
    print(f"  Year:          {result.year}")
    print(f"  Semester:      {result.semester}")
    print(f"  Prerequisites: {result.prerequisites}")
    print(f"  Delivery:      {result.delivery_mode}")
    print(f"  Duration:      {result.duration_weeks} weeks")
    print(f"  Confidence:    {result.confidence:.0%}")
    print(f"  Parser:        {result.parser_used}")

    if result.warnings:
        print("\n  ⚠ Warnings:")
        for w in result.warnings:
            print(f"    - {w}")

    # --- Description ---
    print("\n## DESCRIPTION")
    if result.description:
        # Show first 500 chars
        desc = result.description[:500]
        if len(result.description) > 500:
            desc += f"... ({len(result.description)} chars total)"
        print(f"  {desc}")
    else:
        print("  (none)")

    # --- ULOs ---
    print(f"\n## UNIT LEARNING OUTCOMES ({len(result.learning_outcomes)})")
    for u in result.learning_outcomes:
        print(f"  {u.code}: {u.description}")
        print(f"         Bloom: {u.bloom_level}")

    # --- Assessments ---
    total_weight = sum(a.weight for a in result.assessments)
    print(f"\n## ASSESSMENTS ({len(result.assessments)}, total weight: {total_weight}%)")
    for a in result.assessments:
        due = f"Week {a.due_week}" if a.due_week else "TBD"
        print(f"  [{a.category}] {a.title} — {a.weight}% (due: {due})")
        if a.description:
            print(f"          {a.description[:100]}")

    # --- Weeks ---
    print(f"\n## WEEKLY SCHEDULE ({len(result.weekly_schedule)} weeks)")
    for w in result.weekly_schedule:
        print(f"  Week {w.week_number:2d}: {w.topic}")
        if w.activities:
            for act in w.activities[:2]:
                print(f"           → {act[:80]}")

    # --- Textbooks ---
    print(f"\n## TEXTBOOKS ({len(result.textbooks)})")
    for t in result.textbooks:
        req = "Required" if t.required else "Recommended"
        print(f"  [{req}] {t.title}")
        if t.isbn:
            print(f"          ISBN: {t.isbn}")

    # --- Supplementary ---
    print(f"\n## SUPPLEMENTARY ({len(result.supplementary_info)})")
    for s in result.supplementary_info:
        print(f"  {s.heading}: {s.content[:100]}...")

    print("\n" + "=" * 70)
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
