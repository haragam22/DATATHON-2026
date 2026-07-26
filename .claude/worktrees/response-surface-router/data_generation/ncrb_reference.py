"""Real NCRB "Crime in India" published aggregate statistics.

Numbers only — crime-type frequency %, seasonal / day-of-week / hour-of-day
weighting, district-level volume ratios. No case-level or personally
identifying data of any kind; this file exists to make case_master.py's
sampling distributions defensible ("why is theft 28% of cases") rather than
arbitrary.

TODO(lookups-followup): populate from the latest published NCRB "Crime in
India" volume (state/district tables). Every constant here must cite the
report + table/page it came from in a comment — do not fabricate a
plausible-looking percentage. Until populated, case_master.py should use
its own clearly-labeled placeholder weights, not import from here.
"""

# CRIME_TYPE_FREQUENCY: dict[str, float] — % share of CrimeSubHead volume.
# HOUR_OF_DAY_WEIGHTS: list[float] len 24 — relative incident likelihood.
# DAY_OF_WEEK_WEIGHTS: dict[str, float]
# DISTRICT_VOLUME_RATIO: dict[str, float] — relative case volume per district.
