# Financial Life Projection

An interactive financial planning application that helps you visualize your long-term financial future, including salary growth, mortgage payments, expenses, and savings potential.

## Features

### Income Projection
- Visualize salary growth over 30 years with customizable annual increase rates
- Account for taxes and inflation to see both nominal and real income growth
- Track monthly and annual income changes over time

### Mortgage Analysis
- Dynamic mortgage payment calculation based on loan amount, term, and interest rate
- Visualize amortization schedule showing principal vs. interest payments
- Track remaining balance over the life of the loan
- Calculate total interest paid and percentage of total payments

### Expense Tracking
- Break down monthly expenses across categories (housing, groceries, utilities, etc.)
- Project expenses over time with adjustable cost of living increases
- Visualize the changing composition of expenses as your financial situation evolves

### Savings Potential
- Calculate monthly savings potential (income minus expenses)
- Project cumulative savings over 30 years with compound interest
- Compare savings with and without investment returns
- Adjust investment return rates to see different scenarios
- Account for inflation to see the real value of future savings

### Inflation Impact
- See the effect of inflation on your purchasing power over time
- Compare nominal vs. real values for all financial metrics
- Adjust inflation rates to model different economic scenarios

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Pasnin/financialplan.git
   cd financialplan
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   streamlit run app.py
   ```

4. Open your web browser and navigate to http://localhost:8501

## Usage

The application provides an interactive interface with sliders in the sidebar for adjusting various parameters:

### Salary Parameters
- **Annual Salary Increase (%)**: How much your salary grows each year
- **Tax Rate (%)**: The percentage of your income paid in taxes

### Economic Parameters
- **Annual Inflation Rate (%)**: General rate of price increases over time
- **Annual Cost of Living Increase (%)**: Rate at which your expenses increase
- **Annual Savings Return Rate (%)**: The return on your saved/invested money

### Mortgage Parameters
- **Loan Amount (NOK)**: The principal amount of your mortgage
- **Interest Rate (%)**: The annual interest rate on your mortgage

### Monthly Budget Parameters
- **Fellesgjeld (Building Fees)**: Monthly fees for property maintenance
- **Groceries**: Monthly food expenses
- **Utilities**: Monthly costs for electricity, water, etc.
- **Transportation**: Monthly expenses for commuting, car, etc.
- **Entertainment**: Monthly spending on leisure activities
- **Other Expenses**: Any additional monthly costs

### Interactive Visualizations

The application provides several tabs with different visualizations:

1. **Overview**: Summary of your financial situation with key metrics
2. **Income**: Detailed view of income growth and tax payments
3. **Expenses**: Breakdown of expenses by category
4. **Mortgage**: Mortgage amortization schedule and payments
5. **Savings**: Potential savings and compound interest effects
6. **Inflation Impact**: How inflation affects your finances

## Technical Details

This application is built with:

- **Streamlit**: For the interactive web interface
- **Polars**: For efficient data manipulation
- **Plotly**: For interactive visualizations

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).

---

Created by [Pasnin](https://github.com/Pasnin) 