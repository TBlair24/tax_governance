# import pandas as pd
# from src.quality_checks import check_completeness

# df = pd.read_csv('data/raw/tax_returns.csv')
# issues = check_completeness(df, required_fields=['return_id', 'tin', 'tax_type', 'amount_due_ugx', 'filing_date'])

# for issue in issues:
#     print(f"[{issue['severity']}] {issue['field']} — {issue['affected_rows']} rows missing ({issue['pass_rate']}% pass rate)")


# import pandas as pd
# from src.quality_checks import check_validity

# df = pd.read_csv('data/raw/tax_returns.csv')
# issues = check_validity(df, 'tax_returns')

# for issue in issues:
#     print(f"[{issue['severity']}] {issue['field']} — {issue['affected_rows']} rows ({issue['pass_rate']}% pass rate)")



# import pandas as pd
# from src.quality_checks import check_consistency

# df = pd.read_csv('data/raw/tax_returns.csv')
# issues = check_consistency(df, 'tax_returns')

# for issue in issues:
#     print(f"[{issue['severity']}] {issue['field']} — {issue['affected_rows']} rows ({issue['pass_rate']}% pass rate)")

# import pandas as pd
# from src.quality_checks import check_uniqueness

# df = pd.read_csv('data/raw/tax_returns.csv')
# issues = check_uniqueness(df, key_fields=['return_id'])

# for issue in issues:
#     print(f"[{issue['severity']}] {issue['field']} — {issue['affected_rows']} rows ({issue['pass_rate']}% pass rate)")


# import pandas as pd
# from src.quality_checks import check_timeliness, check_referential_integrity

# returns   = pd.read_csv('data/raw/tax_returns.csv')
# taxpayers = pd.read_csv('data/raw/taxpayer_register.csv')

# for issue in check_timeliness(returns, 'tax_returns'):
#     print(f"[{issue['severity']}] {issue['field']} — {issue['affected_rows']} rows ({issue['pass_rate']}% pass rate)")

# for issue in check_referential_integrity(returns, taxpayers):
#     print(f"[{issue['severity']}] {issue['field']} — {issue['affected_rows']} rows ({issue['pass_rate']}% pass rate)")


from src.quality_checks import run_all_checks

results = run_all_checks()

print(f'Overall DQ Score : {results["overall_dq_score"]}%')
print(f'Total Issues     : {results["total_issues"]}')
print(f'HIGH             : {results["severity_summary"]["HIGH"]}')
print(f'MEDIUM           : {results["severity_summary"]["MEDIUM"]}')
print(f'LOW              : {results["severity_summary"]["LOW"]}')
print()
print('Dimension Scores:')
for dim, score in results['dimension_scores'].items():
    status = '✅' if score >= 95 else ('⚠️' if score >= 80 else '❌')
    print(f'  {status}  {dim:<28} {score}%')


