import numpy as np

# Constants
TICKET_PRICE = 100  # £100 per ticket
RAINY_REFUND = 20 # Assumed RR is 20% of ticket price
cashflow_impact_FP = -100  # False Positive: Unnecessary payout (£100)
cashflow_impact_FN = 100   # False Negative: Missed payout (£100)

# Historical error rates (probabilities)
FP = 0.0472  # Daily FP rate (4.72%)
FN = 0.0786  # Daily FN rate (7.86%)

# Expected PnL impact per day (baseline premium)
expected_pnl = (FP * cashflow_impact_FP) + (FN * cashflow_impact_FN)
expected_pnl_percentage = (expected_pnl / RAINY_REFUND) * 100  # Convert to %

print(f"Expected PnL impact per day: £{expected_pnl:.2f} ({expected_pnl_percentage:.2f}% of Rainy Refund price)")

# Monte Carlo Simulation (1 year = 365 days)
n_simulations = 10000
simulated_pnl = []

for _ in range(n_simulations):
    
    yearly_sim = []
    for day in range(0,365):
        
        # Simulate single festival outcome
        fp_occurred = np.random.random() < FP
        fn_occurred = np.random.random() < FN

        sim_pnl = (fp_occurred * cashflow_impact_FP) + (fn_occurred * cashflow_impact_FN)
        yearly_sim.append(sim_pnl)
    
    simulated_pnl.append(sum(yearly_sim))

# Calculate premium as % of ticket price at confidence intervals
premiums_percentage = {
    "1%": np.percentile(simulated_pnl, 1) / (RAINY_REFUND * 365) * 100,
    "2%": np.percentile(simulated_pnl, 2) / (RAINY_REFUND * 365) * 100,
    "3%": np.percentile(simulated_pnl, 3) / (RAINY_REFUND * 365) * 100,
    "4%": np.percentile(simulated_pnl, 4) / (RAINY_REFUND * 365) * 100,
    "5%": np.percentile(simulated_pnl, 5) / (RAINY_REFUND * 365) * 100,
    "10%": np.percentile(simulated_pnl, 10) / (RAINY_REFUND * 365) * 100,
    "20%": np.percentile(simulated_pnl, 20) / (RAINY_REFUND * 365) * 100,
    "30%": np.percentile(simulated_pnl, 30) / (RAINY_REFUND * 365) * 100,
    "40%": np.percentile(simulated_pnl, 40) / (RAINY_REFUND * 365) * 100,
    "50%": np.percentile(simulated_pnl, 50) / (RAINY_REFUND * 365) * 100
}

print("\nPremium as % of ticket price at confidence intervals:")
for ci, premium in premiums_percentage.items():
    print(f"{ci}: {premium:.2f}%")