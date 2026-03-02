import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for better visualization
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# 1. Create complex synthetic dataset
def create_complex_dataset():
    """Generate a comprehensive dataset for analysis"""
    np.random.seed(42)
    
    # Time series data
    dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='D')
    n_days = len(dates)
    
    # Multiple correlated features
    base_trend = np.linspace(100, 200, n_days) + np.random.normal(0, 10, n_days)
    seasonal_pattern = 20 * np.sin(2 * np.pi * np.arange(n_days) / 365.25)
    
    data = {
        'date': dates,
        'sales': base_trend + seasonal_pattern + np.random.normal(0, 15, n_days),
        'marketing_spend': np.random.uniform(1000, 5000, n_days),
        'website_visits': np.random.poisson(500, n_days),
        'conversion_rate': np.random.beta(2, 8, n_days),
        'customer_satisfaction': np.random.uniform(3.0, 5.0, n_days),
        'product_category': np.random.choice(['Electronics', 'Clothing', 'Home', 'Sports'], n_days),
        'region': np.random.choice(['North', 'South', 'East', 'West'], n_days),
        'is_holiday': np.random.choice([0, 1], n_days, p=[0.95, 0.05]),
        'temperature': np.random.normal(20, 10, n_days)
    }
    
    df = pd.DataFrame(data)
    
    # Add derived columns
    df['revenue_per_visit'] = df['sales'] / df['website_visits']
    df['marketing_efficiency'] = df['sales'] / df['marketing_spend']
    df['month'] = df['date'].dt.month
    df['quarter'] = df['date'].dt.quarter
    df['year'] = df['date'].dt.year
    df['day_of_week'] = df['date'].dt.dayofweek
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    
    return df

# 2. Advanced data cleaning and preprocessing
def advanced_preprocessing(df):
    """Comprehensive data cleaning and feature engineering"""
    
    # Handle missing values
    print("Missing values before cleaning:")
    print(df.isnull().sum())
    
    # Forward fill for time series
    df['sales'] = df['sales'].fillna(method='ffill')
    
    # Interpolate for numerical columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df[col].isnull().any():
            df[col] = df[col].interpolate()
    
    # Remove outliers using IQR method
    def remove_outliers(df, column):
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]
    
    # Apply outlier removal to key metrics
    for col in ['sales', 'marketing_spend', 'website_visits']:
        df = remove_outliers(df, col)
    
    # Create categorical encodings
    df['category_encoded'] = pd.Categorical(df['product_category']).codes
    df['region_encoded'] = pd.Categorical(df['region']).codes
    
    # Create interaction features
    df['marketing_x_holiday'] = df['marketing_spend'] * df['is_holiday']
    df['visits_x_weekend'] = df['website_visits'] * df['is_weekend']
    
    # Rolling averages and trends
    df['sales_7d_avg'] = df['sales'].rolling(window=7).mean()
    df['sales_30d_avg'] = df['sales'].rolling(window=30).mean()
    df['sales_trend'] = df['sales'].pct_change(periods=7)
    
    # Lag features
    for lag in [1, 7, 30]:
        df[f'sales_lag_{lag}'] = df['sales'].shift(lag)
    
    return df

# 3. Complex aggregations and groupby operations
def perform_complex_aggregations(df):
    """Advanced groupby and aggregation operations"""
    
    # Multi-level aggregations
    category_performance = df.groupby(['product_category', 'region']).agg({
        'sales': ['sum', 'mean', 'std', 'count'],
        'marketing_spend': ['sum', 'mean'],
        'website_visits': ['sum', 'mean'],
        'conversion_rate': ['mean', 'median'],
        'customer_satisfaction': ['mean', 'min', 'max']
    }).round(2)
    
    # Time-based aggregations
    monthly_trends = df.groupby(['year', 'month']).agg({
        'sales': 'sum',
        'marketing_spend': 'sum',
        'website_visits': 'sum',
        'customer_satisfaction': 'mean'
    }).reset_index()
    
    # Pivot tables
    sales_pivot = df.pivot_table(
        values='sales',
        index='product_category',
        columns='region',
        aggfunc='sum',
        margins=True,
        margins_name='Total'
    )
    
    # Cross-tabulation
    category_region_crosstab = pd.crosstab(
        df['product_category'], 
        df['region'],
        values=df['sales'],
        aggfunc='mean',
        margins=True
    )
    
    # Custom aggregation functions
    def percentile_75(x):
        return x.quantile(0.75)
    
    def coefficient_of_variation(x):
        return x.std() / x.mean() if x.mean() != 0 else 0
    
    advanced_stats = df.groupby('product_category').agg({
        'sales': ['mean', 'median', percentile_75, coefficient_of_variation],
        'marketing_efficiency': ['mean', 'std'],
        'customer_satisfaction': ['mean', 'min', 'max']
    }).round(3)
    
    return {
        'category_performance': category_performance,
        'monthly_trends': monthly_trends,
        'sales_pivot': sales_pivot,
        'crosstab': category_region_crosstab,
        'advanced_stats': advanced_stats
    }

# 4. Advanced filtering and querying
def advanced_filtering(df):
    """Complex data filtering and querying operations"""
    
    # Multi-condition filtering
    high_performers = df[
        (df['sales'] > df['sales'].quantile(0.75)) &
        (df['customer_satisfaction'] > 4.0) &
        (df['marketing_efficiency'] > 0.05)
    ]
    
    # Query method for complex conditions
    weekend_analysis = df.query(
        "is_weekend == 1 and is_holiday == 1 and sales > sales.mean()"
    )
    
    # Boolean indexing with multiple conditions
    seasonal_patterns = df[
        (df['month'].isin([11, 12, 1])) &  # Winter months
        (df['product_category'] == 'Electronics') &
        (df['region'].isin(['North', 'East']))
    ]
    
    # Using isin for categorical filtering
    top_categories = df[df['product_category'].isin(
        df['product_category'].value_counts().head(2).index
    )]
    
    # Complex string operations (if we had string columns)
    # Here we'll simulate with categorical data
    category_analysis = df[df['product_category'].str.contains('Elect|Cloth', na=False)]
    
    return {
        'high_performers': high_performers,
        'weekend_analysis': weekend_analysis,
        'seasonal_patterns': seasonal_patterns,
        'top_categories': top_categories,
        'category_analysis': category_analysis
    }

# 5. Time series analysis
def time_series_analysis(df):
    """Comprehensive time series analysis"""
    
    # Set date as index
    df_ts = df.set_index('date').sort_index()
    
    # Resampling at different frequencies
    daily_sales = df_ts['sales'].resample('D').mean()
    weekly_sales = df_ts['sales'].resample('W').sum()
    monthly_sales = df_ts['sales'].resample('M').sum()
    quarterly_sales = df_ts['sales'].resample('Q').sum()
    
    # Moving averages with different windows
    df_ts['sales_ma_7'] = df_ts['sales'].rolling(window=7).mean()
    df_ts['sales_ma_30'] = df_ts['sales'].rolling(window=30).mean()
    df_ts['sales_ma_90'] = df_ts['sales'].rolling(window=90).mean()
    
    # Exponential moving average
    df_ts['sales_ema'] = df_ts['sales'].ewm(span=20, adjust=False).mean()
    
    # Year-over-year comparison
    yearly_comparison = df_ts.groupby(df_ts.index.year)['sales'].sum().pct_change()
    
    # Seasonal decomposition preparation
    monthly_avg = df_ts.groupby(df_ts.index.month)['sales'].mean()
    
    return {
        'daily_sales': daily_sales,
        'weekly_sales': weekly_sales,
        'monthly_sales': monthly_sales,
        'quarterly_sales': quarterly_sales,
        'moving_averages': df_ts[['sales', 'sales_ma_7', 'sales_ma_30', 'sales_ma_90', 'sales_ema']].tail(30),
        'yearly_growth': yearly_comparison,
        'seasonal_pattern': monthly_avg
    }

# 6. Statistical analysis and correlations
def statistical_analysis(df):
    """Advanced statistical analysis"""
    
    # Correlation matrix
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    correlation_matrix = df[numeric_cols].corr()
    
    # Find highly correlated features
    high_correlations = correlation_matrix.abs() > 0.7
    correlated_pairs = []
    
    for i in range(len(correlation_matrix.columns)):
        for j in range(i+1, len(correlation_matrix.columns)):
            if high_correlations.iloc[i, j]:
                correlated_pairs.append((
                    correlation_matrix.columns[i],
                    correlation_matrix.columns[j],
                    correlation_matrix.iloc[i, j]
                ))
    
    # Descriptive statistics by category
    desc_stats = df.groupby('product_category')[numeric_cols].describe().transpose()
    
    # Hypothesis testing simulation (t-tests between groups)
    from scipy import stats
    
    # Compare sales between categories
    categories = df['product_category'].unique()
    category_comparisons = {}
    
    for i, cat1 in enumerate(categories):
        for cat2 in categories[i+1:]:
            sales1 = df[df['product_category'] == cat1]['sales']
            sales2 = df[df['product_category'] == cat2]['sales']
            t_stat, p_value = stats.ttest_ind(sales1, sales2)
            category_comparisons[f"{cat1}_vs_{cat2}"] = {
                't_statistic': t_stat,
                'p_value': p_value,
                'significant': p_value < 0.05
            }
    
    return {
        'correlation_matrix': correlation_matrix,
        'correlated_pairs': correlated_pairs,
        'descriptive_stats': desc_stats,
        'hypothesis_tests': category_comparisons
    }

# 7. Data visualization preparation
def prepare_visualization_data(df):
    """Prepare data for various visualizations"""
    
    # Time series data for plotting
    time_series_data = df.set_index('date')[['sales', 'marketing_spend', 'website_visits']]
    
    # Category performance data
    category_summary = df.groupby('product_category').agg({
        'sales': 'sum',
        'marketing_spend': 'sum',
        'customer_satisfaction': 'mean',
        'conversion_rate': 'mean'
    }).round(2)
    
    # Regional performance
    regional_summary = df.groupby('region').agg({
        'sales': 'sum',
        'marketing_efficiency': 'mean',
        'customer_satisfaction': 'mean'
    }).round(2)
    
    # Monthly trends
    monthly_data = df.groupby(['year', 'month']).agg({
        'sales': 'sum',
        'marketing_spend': 'sum',
        'website_visits': 'sum'
    }).reset_index()
    monthly_data['date'] = pd.to_datetime(monthly_data[['year', 'month']].assign(day=1))
    
    return {
        'time_series': time_series_data,
        'category_summary': category_summary,
        'regional_summary': regional_summary,
        'monthly_trends': monthly_data
    }

# 8. Export and reporting functions
def generate_reports(df, analysis_results):
    """Generate comprehensive reports"""
    
    # Summary statistics
    summary_stats = df.describe(include='all').transpose()
    
    # Data quality report
    quality_report = pd.DataFrame({
        'column': df.columns,
        'data_type': df.dtypes,
        'missing_values': df.isnull().sum(),
        'missing_percentage': (df.isnull().sum() / len(df) * 100).round(2),
        'unique_values': df.nunique(),
        'memory_usage': df.memory_usage(deep=True)
    })
    
    # Performance metrics
    performance_metrics = pd.DataFrame({
        'metric': ['Total Sales', 'Avg Daily Sales', 'Total Marketing Spend', 
                   'Avg Conversion Rate', 'Avg Customer Satisfaction'],
        'value': [
            df['sales'].sum(),
            df['sales'].mean(),
            df['marketing_spend'].sum(),
            df['conversion_rate'].mean(),
            df['customer_satisfaction'].mean()
        ]
    }).round(2)
    
    return {
        'summary_stats': summary_stats,
        'quality_report': quality_report,
        'performance_metrics': performance_metrics
    }

# Main execution function
def main():
    """Execute the complete pandas analysis pipeline"""
    
    print("=" * 60)
    print("COMPLEX PANDAS DATA ANALYSIS PIPELINE")
    print("=" * 60)
    
    # 1. Create dataset
    print("\n1. Creating complex dataset...")
    df = create_complex_dataset()
    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # 2. Preprocessing
    print("\n2. Performing advanced preprocessing...")
    df_clean = advanced_preprocessing(df.copy())
    print(f"Clean dataset shape: {df_clean.shape}")
    
    # 3. Aggregations
    print("\n3. Performing complex aggregations...")
    aggregation_results = perform_complex_aggregations(df_clean)
    print(f"Category performance shape: {aggregation_results['category_performance'].shape}")
    
    # 4. Filtering
    print("\n4. Applying advanced filters...")
    filtering_results = advanced_filtering(df_clean)
    print(f"High performers count: {len(filtering_results['high_performers'])}")
    
    # 5. Time series analysis
    print("\n5. Conducting time series analysis...")
    ts_results = time_series_analysis(df_clean)
    print(f"Monthly sales data points: {len(ts_results['monthly_sales'])}")
    
    # 6. Statistical analysis
    print("\n6. Performing statistical analysis...")
    stats_results = statistical_analysis(df_clean)
    print(f"Found {len(stats_results['correlated_pairs'])} correlated feature pairs")
    
    # 7. Visualization data
    print("\n7. Preparing visualization data...")
    viz_data = prepare_visualization_data(df_clean)
    print(f"Time series data shape: {viz_data['time_series'].shape}")
    
    # 8. Generate reports
    print("\n8. Generating comprehensive reports...")
    reports = generate_reports(df_clean, {
        'aggregations': aggregation_results,
        'filtering': filtering_results,
        'time_series': ts_results,
        'statistics': stats_results,
        'visualization': viz_data
    })
    
    # Display key results
    print("\n" + "=" * 60)
    print("KEY RESULTS SUMMARY")
    print("=" * 60)
    
    print("\nTop 5 correlated feature pairs:")
    for pair in stats_results['correlated_pairs'][:5]:
        print(f"  {pair[0]} ↔ {pair[1]}: {pair[2]:.3f}")
    
    print("\nCategory Performance (Top 3 by sales):")
    top_categories = aggregation_results['category_performance']['sales']['sum'].nlargest(3)
    print(top_categories)
    
    print("\nData Quality Overview:")
    print(reports['quality_report'][['column', 'missing_percentage', 'unique_values']].head(10))
    
    print("\nPerformance Metrics:")
    print(reports['performance_metrics'])
    
    print("\nMonthly Sales Trend (Last 6 months):")
    print(ts_results['monthly_sales'].tail(6))
    
    # Save results to files
    print("\n9. Saving results to files...")
    
    # Save main dataset
    df_clean.to_csv('processed_dataset.csv', index=False)
    
    # Save correlation matrix
    stats_results['correlation_matrix'].to_csv('correlation_matrix.csv')
    
    # Save category performance
    aggregation_results['category_performance'].to_csv('category_performance.csv')
    
    # Save reports
    reports['summary_stats'].to_csv('summary_statistics.csv')
    reports['quality_report'].to_csv('data_quality_report.csv')
    reports['performance_metrics'].to_csv('performance_metrics.csv', index=False)
    
    print("All files saved successfully!")
    
    return {
        'dataset': df_clean,
        'aggregations': aggregation_results,
        'filtering': filtering_results,
        'time_series': ts_results,
        'statistics': stats_results,
        'visualization': viz_data,
        'reports': reports
    }

# Execute the analysis
if __name__ == "__main__":
    results = main()
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE!")
    print("=" * 60)
    print("\nFiles generated:")
    print("- processed_dataset.csv")
    print("- correlation_matrix.csv") 
    print("- category_performance.csv")
    print("- summary_statistics.csv")
    print("- data_quality_report.csv")
    print("- performance_metrics.csv")
    print("\nAccess the results dictionary 'results' for further analysis!")