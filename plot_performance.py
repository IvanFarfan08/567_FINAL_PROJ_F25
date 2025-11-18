"""
Script to plot performance testing results
Reads from performance_results.csv and creates a visualization
Source: ChatGPT
"""
import pandas as pd
import matplotlib.pyplot as plt


def plot_performance_results():
    """Create performance visualization from CSV data"""
    # Read the CSV data
    df = pd.read_csv('performance_results.csv')

    # Create the plot
    plt.figure(figsize=(14, 8))

    # Plot all four curves
    plt.plot(df['Records'], df['Encode_No_Tests'],
             marker='o', linewidth=2, markersize=7,
             label='Encode Without Tests',
             color='#2E86AB', linestyle='-')

    plt.plot(df['Records'], df['Encode_With_Tests'],
             marker='s', linewidth=2, markersize=7,
             label='Encode With Tests',
             color='#A23B72', linestyle='-')

    plt.plot(df['Records'], df['Decode_No_Tests'],
             marker='^', linewidth=2, markersize=7,
             label='Decode Without Tests',
             color='#F18F01', linestyle='--')

    plt.plot(df['Records'], df['Decode_With_Tests'],
             marker='D', linewidth=2, markersize=7,
             label='Decode With Tests',
             color='#C73E1D', linestyle='--')

    # Customize the plot
    plt.xlabel('Number of Records Processed', fontsize=12, fontweight='bold')
    plt.ylabel('Execution Time (seconds)', fontsize=12, fontweight='bold')
    plt.title('MRTD.py Performance: Encoding and Decoding Time vs Number of Records',
              fontsize=14, fontweight='bold', pad=20)

    # Add grid for better readability
    plt.grid(True, alpha=0.3, linestyle='--')

    # Add legend
    plt.legend(fontsize=11, loc='upper left', framealpha=0.9)

    # Set x-axis ticks to show all test points
    plt.xticks(df['Records'], rotation=45)

    # Format y-axis to show more decimal places for small values
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.3f}'))

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    # Save the plot
    plt.savefig('performance_plot.png', dpi=300, bbox_inches='tight')
    print("Plot saved as performance_plot.png")

    # plt.show()
if __name__ == "__main__":
    plot_performance_results()  
