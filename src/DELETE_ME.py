

# Quanty doc for analyzing forecast accuracy

# external imports
import pandas as pd
import os
import numpy as np
import logging

# binary classification metrics import
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

# for plots
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from sklearn.metrics import roc_curve, roc_auc_score
from sklearn.utils import resample

# Set logging to INFO if ran on the cmd
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def binary_classification_metrics(forecast_arr, actuals_arr, threshold):

    actual_binary = (actuals_arr >= threshold).astype(int)
    forecast_binary = (forecast_arr >= threshold).astype(int)

    print("Confusion Matrix:\n", confusion_matrix(actual_binary, forecast_binary))
    print("Precision (Avoid False Alarms):", precision_score(actual_binary, forecast_binary))
    print("Recall (Capture True Events):", recall_score(actual_binary, forecast_binary))
    print("F1-Score (Balance):", f1_score(actual_binary, forecast_binary))


def threshold_metrics(actuals_arr, forecast_arr, threshold):
    TP = ((actuals_arr >= threshold) & (forecast_arr >= threshold)).sum()
    FN = ((actuals_arr >= threshold) & (forecast_arr < threshold)).sum()
    FP = ((actuals_arr < threshold) & (forecast_arr >= threshold)).sum()
    
    hit_rate = TP / (TP + FN) if (TP + FN) > 0 else np.nan
    false_alarm_rate = FP / (FP + (actuals_arr < threshold).sum()) if FP > 0 else np.nan
    
    print(f"Hit Rate: {hit_rate:.2%}, False Alarm Rate: {false_alarm_rate:.2%}")


def plot(actual, forecast, threshold):

    # Create plot
    colors = np.where((actual >= threshold) & (forecast >= threshold), 'blue', 
                 np.where((actual >= threshold) | (forecast >= threshold), 'red', 'gray'))
    plt.figure(figsize=(10, 6))
    plt.scatter(actual, forecast, c=colors, alpha=0.7, edgecolors='w', linewidth=0.5)
    plt.axhline(threshold, color='black', linestyle='--', label=f'Threshold ({threshold})')
    plt.axvline(threshold, color='black', linestyle='--')

    # Custom legend
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Correct Detection (Both ≥ threshold)',
            markerfacecolor='blue', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Error (One ≥ threshold)',
            markerfacecolor='red', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Both < threshold',
            markerfacecolor='gray', markersize=10)
    ]

    # Create fig
    plt.legend(handles=legend_elements)
    plt.xlabel("Actual Value")
    plt.ylabel("Forecast Value")
    plt.title("Forecast vs Actual (Threshold Analysis)")
    plt.grid(True, alpha=0.3)

    # Save the figure
    plt.savefig(os.path.join(os.getcwd(),'data/temp', 'forecast_vs_actual_threshold_analysis.png'), 
                dpi=300, 
                bbox_inches='tight',  # prevents cropping of labels
                transparent=False)



def roc_plot(actuals_arr, forecast_arr, threshold):

    actual_binary = (actuals_arr >= threshold).astype(int)

    fpr, tpr, thresholds = roc_curve(actual_binary, forecast_arr)
    auc = roc_auc_score(actual_binary, forecast_arr)

    plt.figure()
    plt.plot(fpr, tpr, label=f'AUC = {auc:.2f}')
    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve (Threshold Sensitivity)")
    plt.legend()
        # Save the figure
    plt.savefig(os.path.join(os.getcwd(),'data/temp', 'roc.png'), 
                dpi=300, 
                bbox_inches='tight',  # prevents cropping of labels
                transparent=False)

def pod_csi(actual, forecast, threshold):
    hits = ((actual >= threshold) & (forecast >= threshold)).sum()
    misses = ((actual >= threshold) & (forecast < threshold)).sum()
    false_alarms = ((actual < threshold) & (forecast >= threshold)).sum()
    
    POD = hits / (hits + misses)
    CSI = hits / (hits + misses + false_alarms)
    return POD, CSI
    

def bootstrap_metric(actuals_arr, forecast_arr, n_iter=1000):

    metric_func = lambda a, f: pod_csi(a, f, threshold=5)[0]

    metrics = []
    for _ in range(n_iter):
        a_resample, f_resample = resample(actuals_arr, forecast_arr)
        metrics.append(metric_func(a_resample, f_resample))
    percentiles = np.percentile(metrics, [2.5, 97.5])

    print(f"POD 95% CI: [{percentiles[0]:.2%}, {percentiles[1]:.2%}]")


def accuracy_on_trigger(df, trigger_mm_float):

    """Function to get the accuracy around a particular trigger"""

    # get forecast and actuals arr
    forecast_np_arr = np.array(df["thickness_of_rainfall_amount_mm"].values)
    actuals_np_arr = np.array(df["precipitation_mm"].values)

    # Binary classification analysis print
    binary_classification_metrics(forecast_np_arr, actuals_np_arr, trigger_mm_float)

    # Hit Rate print
    threshold_metrics(actuals_np_arr, forecast_np_arr, trigger_mm_float)

    # Show percentiles
    bootstrap_metric(actuals_np_arr, forecast_np_arr, n_iter=100000)

    # Create plot
    plot(actuals_np_arr, forecast_np_arr, trigger_mm_float)
    roc_plot(actuals_np_arr, forecast_np_arr, trigger_mm_float)

if __name__ == "__main__":

    # Set example variables
    fn = "total.csv"
    df = pd.read_csv(os.path.join(os.getcwd(),"data/temp",fn))
    df["precipitation_mm"] = pd.to_numeric(df["precipitation_mm"], errors='coerce')
    df["thickness_of_rainfall_amount_mm"] = pd.to_numeric(df["thickness_of_rainfall_amount_mm"], errors='coerce')
    trigger_mm_float = 2.5

    accuracy_on_trigger(df, trigger_mm_float)