import numpy as np

# Constants
TICKET_PRICE = 100  # £100 per ticket
RAINY_REFUND = 20 # Assumed RR is 20% of ticket price
cashflow_impact_FP = -100  # False Positive: Unnecessary payout (£100)
cashflow_impact_FN = 100   # False Negative: Missed payout (£100)

# Historical error rates (probabilities)
FP = 0.05048  # Daily FP rate (5.048%)
FN = 0.06124  # Daily FN rate (6.124%)

# Expected PnL impact per day (baseline premium)
expected_pnl = (FP * cashflow_impact_FP) + (FN * cashflow_impact_FN)
expected_pnl_percentage = (expected_pnl / RAINY_REFUND) * 100  # Convert to %

print(f"Expected PnL impact per day: £{expected_pnl:.2f} ({expected_pnl_percentage:.2f}% of Rainy Refund price)")

# Monte Carlo Simulation (1 year = 180 days) - summer only
n_simulations = 500000
simulated_pnl = []

for _ in range(n_simulations):
    
    yearly_sim = []
    for day in range(0,180):
        
        # Simulate single festival outcome
        fp_occurred = np.random.random() < FP
        fn_occurred = np.random.random() < FN

        sim_pnl = (fp_occurred * cashflow_impact_FP) + (fn_occurred * cashflow_impact_FN)
        yearly_sim.append(sim_pnl)
    
    simulated_pnl.append(sum(yearly_sim))

# Calculate premium as % of ticket price at confidence intervals
arr = [10,20,25,30,40,50]

premiums_percentage = {
    f"{i}%": np.percentile(simulated_pnl, i) / (RAINY_REFUND * 180) * 100
    for i in arr
}

print("\nPremium as % of ticket price at confidence intervals:")
for ci, premium in premiums_percentage.items():
    print(f"{ci}: {premium:.2f}%")