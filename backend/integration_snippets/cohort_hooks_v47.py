"""Bind habit plans to cohort enrollment lifecycle.

Recommended hooks:
- on cohort enrollment activated -> provision default habit plan templates
- on checkpoint completed -> optionally auto-create check-in/journal prompt
- on cohort archived -> deactivate linked habit plans
"""
