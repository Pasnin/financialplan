import streamlit as st
import polars as pl
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(
    page_title='Financial Life Projection',
    layout='wide'
)

# App title and description
st.title('Income, Mortgage and Savings Projection')
st.write('Visualize your salary growth, mortgage payments, and savings potential over time')

# Sidebar with sliders for inputs
st.sidebar.header('Salary Parameters')
base_salary = 675000  # NOK
st.sidebar.write(f'Base Salary: {base_salary:,} NOK')

annual_increase = st.sidebar.slider(
    'Annual Salary Increase (%)',
    min_value=0.0,
    max_value=10.0,
    value=3.0,
    step=0.1
)

tax_rate = st.sidebar.slider(
    'Tax Rate (%)',
    min_value=10.0,
    max_value=50.0,
    value=21.0,
    step=0.1
)

# Economic parameters
st.sidebar.header('Economic Parameters')
inflation_rate = st.sidebar.slider(
    'Annual Inflation Rate (%)',
    min_value=0.0,
    max_value=10.0,
    value=2.0,
    step=0.1
)

cost_of_living_increase = st.sidebar.slider(
    'Annual Cost of Living Increase (%)',
    min_value=0.0, 
    max_value=10.0,
    value=2.5,
    step=0.1,
    help='Rate at which expenses increase, often slightly higher than inflation'
)

savings_return_rate = st.sidebar.slider(
    'Annual Savings Return Rate (%)',
    min_value=0.0,
    max_value=15.0,
    value=3.0,
    step=0.1,
    help='Annual return rate on accumulated savings (compound interest)'
)

# Mortgage parameters
st.sidebar.header('Mortgage Parameters')
loan_amount = st.sidebar.number_input('Loan Amount (NOK)', value=2000000, step=10000)
loan_term_years = 30
interest_rate = st.sidebar.slider('Interest Rate (%)', min_value=2.0, max_value=10.0, value=5.79, step=0.01)

# Calculate monthly mortgage payment using the amortization formula
def calculate_monthly_payment(principal, annual_rate, term_years):
    if annual_rate == 0:
        return principal / (term_years * 12)
    
    monthly_rate = annual_rate / 100 / 12
    num_payments = term_years * 12
    
    # Formula: P * [r(1+r)^n] / [(1+r)^n - 1]
    payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
    return payment

monthly_payment = calculate_monthly_payment(loan_amount, interest_rate, loan_term_years)

# Display the calculated monthly payment
st.sidebar.write(f'Monthly Payment: {monthly_payment:,.0f} NOK')

# Budget parameters
st.sidebar.header('Monthly Budget Parameters')
joint_dept = st.sidebar.slider('joint_dept (Building Fees) (NOK/month)', min_value=0, max_value=10000, value=2750, step=50)
groceries = st.sidebar.slider('Groceries (NOK/month)', min_value=0, max_value=10000, value=5000, step=100)
utilities = st.sidebar.slider('Utilities (NOK/month)', min_value=0, max_value=5000, value=2000, step=100)
transportation = st.sidebar.slider('Transportation (NOK/month)', min_value=0, max_value=5000, value=1500, step=100)
entertainment = st.sidebar.slider('Entertainment (NOK/month)', min_value=0, max_value=5000, value=2000, step=100)
other_expenses = st.sidebar.slider('Other Expenses (NOK/month)', min_value=0, max_value=10000, value=3000, step=100)

# Calculate total monthly expenses (excluding mortgage)
monthly_expenses = joint_dept + groceries + utilities + transportation + entertainment + other_expenses

# Create mortgage amortization schedule
def calculate_mortgage_schedule(loan_amount, annual_interest_rate, term_years):
    monthly_interest_rate = annual_interest_rate / 100 / 12
    total_payments = term_years * 12
    
    # Calculate monthly payment
    if annual_interest_rate == 0:
        monthly_payment = loan_amount / total_payments
    else:
        monthly_payment = calculate_monthly_payment(loan_amount, annual_interest_rate, term_years)
    
    remaining_balance = loan_amount
    schedule = []
    
    for payment_num in range(1, total_payments + 1):
        interest_payment = remaining_balance * monthly_interest_rate
        principal_payment = monthly_payment - interest_payment
        
        if principal_payment > remaining_balance:
            principal_payment = remaining_balance
            monthly_payment = principal_payment + interest_payment
            
        remaining_balance -= principal_payment
        
        if remaining_balance < 0:
            remaining_balance = 0
            
        year = (payment_num - 1) // 12 + 1
        
        schedule.append({
            'Payment_Number': payment_num,
            'Year': year,
            'Monthly_Payment': monthly_payment,
            'Principal_Payment': principal_payment,
            'Interest_Payment': interest_payment,
            'Remaining_Balance': remaining_balance
        })
    
    return schedule

# Generate projections for 30 years
years = list(range(1, 31))
financial_data = []

# Initialize values
current_salary = base_salary
current_expenses = {
    'Joint Dept': joint_dept,
    'groceries': groceries,
    'utilities': utilities,
    'transportation': transportation,
    'entertainment': entertainment,
    'other_expenses': other_expenses
}

# Calculate mortgage data
mortgage_schedule = calculate_mortgage_schedule(loan_amount, interest_rate, loan_term_years)
mortgage_df = pl.DataFrame(mortgage_schedule)

# Aggregate mortgage data by year
mortgage_yearly = (mortgage_df
    .group_by('Year')
    .agg([
        pl.col('Monthly_Payment').sum().alias('Annual_Mortgage_Payment'),
        pl.col('Principal_Payment').sum().alias('Annual_Principal'),
        pl.col('Interest_Payment').sum().alias('Annual_Interest')
    ])
    .with_columns(pl.col('Year').cast(pl.Int64))
    .sort('Year')
)

# Get remaining balance at the end of each year
remaining_balance_yearly = (mortgage_df
    .filter(pl.col('Payment_Number') % 12 == 0)
    .select(['Year', pl.col('Remaining_Balance').alias('Year_End_Balance')])
)

# If the loan term is not a multiple of 12, add the last payment
if len(remaining_balance_yearly) < loan_term_years:
    last_payment = mortgage_df.tail(1)
    remaining_balance_yearly = pl.concat([
        remaining_balance_yearly,
        pl.DataFrame({
            'Year': last_payment['Year'],
            'Year_End_Balance': last_payment['Remaining_Balance']
        })
    ])

# Join the mortgage data
mortgage_yearly = mortgage_yearly.join(remaining_balance_yearly, on='Year', how='left')
mortgage_yearly = mortgage_yearly.fill_null(0)

# Generate financial projections year by year
cumulative_savings = 0
for year in years:
    # Calculate salary for this year
    gross_salary = current_salary
    net_salary = gross_salary * (1 - tax_rate/100)
    
    # Calculate monthly values
    gross_monthly = gross_salary / 12
    net_monthly = net_salary / 12
    
    # Get expense values for this year
    if year == 1:
        year_expenses = current_expenses.copy()
        monthly_total_expenses = sum(year_expenses.values())
        annual_total_expenses = monthly_total_expenses * 12
    else:
        # Apply cost of living increase
        for category in current_expenses:
            current_expenses[category] *= (1 + cost_of_living_increase/100)
        
        year_expenses = current_expenses.copy()
        monthly_total_expenses = sum(year_expenses.values())
        annual_total_expenses = monthly_total_expenses * 12
    
    # Get mortgage data for this year
    if year <= len(mortgage_yearly):
        mortgage_row = mortgage_yearly.filter(pl.col('Year') == year)
        annual_mortgage = mortgage_row['Annual_Mortgage_Payment'][0]
        annual_principal = mortgage_row['Annual_Principal'][0]
        annual_interest = mortgage_row['Annual_Interest'][0]
        remaining_balance = mortgage_row['Year_End_Balance'][0]
        monthly_mortgage = annual_mortgage / 12
    else:
        annual_mortgage = 0
        annual_principal = 0
        annual_interest = 0
        remaining_balance = 0
        monthly_mortgage = 0
    
    # Calculate total monthly outflow (all expenses + mortgage)
    monthly_outflow = monthly_total_expenses + monthly_mortgage
    annual_outflow = monthly_outflow * 12
    
    # Calculate savings potential
    monthly_savings_potential = net_monthly - monthly_outflow
    annual_savings_potential = monthly_savings_potential * 12
    
    # Calculate inflation factor
    inflation_factor = (1 / (1 + inflation_rate/100) ** (year - 1))
    
    # Calculate real (inflation-adjusted) values
    real_net_salary = net_salary * inflation_factor
    real_gross_monthly = gross_monthly * inflation_factor
    real_net_monthly = net_monthly * inflation_factor
    real_monthly_expenses = monthly_total_expenses * inflation_factor
    real_monthly_mortgage = monthly_mortgage * inflation_factor
    real_monthly_savings = monthly_savings_potential * inflation_factor
    
    # Calculate cumulative savings with compound interest
    if year == 1:
        cumulative_savings = annual_savings_potential
    else:
        # Apply return rate to existing savings, then add new savings
        cumulative_savings = cumulative_savings * (1 + savings_return_rate/100) + annual_savings_potential
    
    # Calculate real cumulative savings (adjusted for inflation)
    real_cumulative_savings = cumulative_savings * inflation_factor
    
    # Store the data
    financial_data.append({
        'Year': year,
        'Gross_Salary': gross_salary,
        'Net_Salary': net_salary,
        'Gross_Monthly': gross_monthly,
        'Net_Monthly': net_monthly,
        'Joint Dept': year_expenses['Joint Dept'],
        'Groceries': year_expenses['groceries'],
        'Utilities': year_expenses['utilities'],
        'Transportation': year_expenses['transportation'],
        'Entertainment': year_expenses['entertainment'],
        'Other_Expenses': year_expenses['other_expenses'],
        'Monthly_Expenses': monthly_total_expenses,
        'Annual_Expenses': annual_total_expenses,
        'Monthly_Mortgage': monthly_mortgage,
        'Annual_Mortgage': annual_mortgage,
        'Annual_Principal': annual_principal,
        'Annual_Interest': annual_interest,
        'Remaining_Balance': remaining_balance,
        'Monthly_Outflow': monthly_outflow,
        'Annual_Outflow': annual_outflow,
        'Monthly_Savings': monthly_savings_potential,
        'Annual_Savings': annual_savings_potential,
        'Cumulative_Savings': cumulative_savings,
        'Real_Cumulative_Savings': real_cumulative_savings,
        'Inflation_Factor': inflation_factor,
        'Real_Net_Salary': real_net_salary,
        'Real_Monthly_Income': real_net_monthly,
        'Real_Monthly_Expenses': real_monthly_expenses,
        'Real_Monthly_Mortgage': real_monthly_mortgage,
        'Real_Monthly_Savings': real_monthly_savings
    })
    
    # Update salary for next year
    current_salary *= (1 + annual_increase/100)

# Convert to DataFrame
df = pl.DataFrame(financial_data)

# Display data in tabs
st.subheader('Financial Projections Over 30 Years')
tabs = st.tabs(['Overview', 'Income', 'Expenses', 'Mortgage', 'Savings', 'Inflation Impact'])

with tabs[0]:
    # Show key metrics for the first year
    st.write("### Current Financial Snapshot (Year 1)")
    
    # First row - income and expenses
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Monthly Net Income", f"{df['Net_Monthly'][0]:,.0f} NOK")
    
    with col2:
        st.metric("Monthly Expenses", f"{df['Monthly_Expenses'][0]:,.0f} NOK")
    
    with col3:
        st.metric("Monthly Mortgage", f"{df['Monthly_Mortgage'][0]:,.0f} NOK")
    
    with col4:
        st.metric("Monthly Savings Potential", f"{df['Monthly_Savings'][0]:,.0f} NOK")
    
    # Show overview of financial projection
    st.write("### Financial Overview Over Time")
    
    # Create overview visualization
    fig_overview = go.Figure()
    
    # Add net income line
    fig_overview.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['Net_Monthly'],
            name='Net Monthly Income',
            line=dict(color='blue', width=2),
            hovertemplate='Year %{x}<br>Net Income: %{y:,.0f} NOK<extra></extra>'
        )
    )
    
    # Add stacked bar for expenses
    fig_overview.add_trace(
        go.Bar(
            x=df['Year'],
            y=df['Monthly_Mortgage'],
            name='Mortgage',
            marker_color='red',
            hovertemplate='Year %{x}<br>Mortgage: %{y:,.0f} NOK<extra></extra>'
        )
    )
    
    fig_overview.add_trace(
        go.Bar(
            x=df['Year'],
            y=df['Monthly_Expenses'],
            name='Living Expenses',
            marker_color='orange',
            hovertemplate='Year %{x}<br>Expenses: %{y:,.0f} NOK<extra></extra>'
        )
    )
    
    # Add savings line
    fig_overview.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['Monthly_Savings'],
            name='Monthly Savings',
            line=dict(color='green', width=2),
            hovertemplate='Year %{x}<br>Savings: %{y:,.0f} NOK<extra></extra>'
        )
    )
    
    # Customize layout
    fig_overview.update_layout(
        title='Monthly Financial Overview',
        xaxis_title='Year',
        yaxis_title='NOK per Month',
        barmode='stack',
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig_overview, use_container_width=True)
    
    # Display summary data table
    st.write("### Summary Data")
    summary_df = df.select([
        'Year', 
        'Net_Monthly', 
        'Monthly_Expenses', 
        'Monthly_Mortgage', 
        'Monthly_Savings',
        'Remaining_Balance',
        'Cumulative_Savings'
    ])
    
    st.dataframe(summary_df.with_columns([
        pl.col('Net_Monthly').round(0),
        pl.col('Monthly_Expenses').round(0),
        pl.col('Monthly_Mortgage').round(0),
        pl.col('Monthly_Savings').round(0),
        pl.col('Remaining_Balance').round(0),
        pl.col('Cumulative_Savings').round(0)
    ]))

with tabs[1]:
    # Income visualization
    st.write("### Income Growth Over Time")
    
    # Create income visualization
    fig_income = go.Figure()
    
    # Add gross salary
    fig_income.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['Gross_Salary'],
            name='Gross Annual Salary',
            line=dict(color='darkblue', width=2),
            hovertemplate='Year %{x}<br>Gross Salary: %{y:,.0f} NOK<extra></extra>'
        )
    )
    
    # Add net salary
    fig_income.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['Net_Salary'],
            name='Net Annual Salary',
            line=dict(color='blue', width=2),
            hovertemplate='Year %{x}<br>Net Salary: %{y:,.0f} NOK<extra></extra>'
        )
    )
    
    # Add real net salary
    fig_income.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['Real_Net_Salary'],
            name='Real Net Salary (Inflation Adjusted)',
            line=dict(color='lightblue', width=2, dash='dash'),
            hovertemplate='Year %{x}<br>Real Net Salary: %{y:,.0f} NOK<extra></extra>'
        )
    )
    
    # Add tax as area
    fig_income.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['Gross_Salary']-df['Net_Salary'],
            name='Tax Amount',
            fill='tozeroy',
            line=dict(color='red', width=0),
            hovertemplate='Year %{x}<br>Tax: %{y:,.0f} NOK<extra></extra>'
        )
    )
    
    # Customize layout
    fig_income.update_layout(
        title='Annual Income Growth with Inflation Adjustment',
        xaxis_title='Year',
        yaxis_title='NOK per Year',
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig_income, use_container_width=True)
    
    # Show monthly income growth
    fig_monthly_income = go.Figure()
    
    fig_monthly_income.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['Net_Monthly'],
            name='Nominal Net Monthly',
            line=dict(color='blue', width=2),
            hovertemplate='Year %{x}<br>Net Monthly: %{y:,.0f} NOK<extra></extra>'
        )
    )
    
    fig_monthly_income.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['Real_Monthly_Income'],
            name='Real Net Monthly (Inflation Adjusted)',
            line=dict(color='blue', width=2, dash='dash'),
            hovertemplate='Year %{x}<br>Real Monthly: %{y:,.0f} NOK<extra></extra>'
        )
    )
    
    # Customize layout
    fig_monthly_income.update_layout(
        title='Monthly Income Growth (Nominal vs Real)',
        xaxis_title='Year',
        yaxis_title='NOK per Month',
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig_monthly_income, use_container_width=True)

with tabs[2]:
    # Expenses visualization
    st.write("### Monthly Expenses Breakdown")
    
    # Create pie chart for first year expenses - fixing the column names
    expense_categories = ['Mortgage', 'Joint Dept', 'Groceries', 'Utilities', 'Transportation', 'Entertainment', 'Other_Expenses']
    expense_values = []
    
    # Add mortgage separately since it's stored in a different column name
    expense_values.append(df['Monthly_Mortgage'][0])
    
    # Add the rest of the expense categories
    for cat in expense_categories[1:]:
        expense_values.append(df[cat][0])
    
    fig_expense_pie = go.Figure(data=[go.Pie(
        labels=expense_categories,
        values=expense_values,
        hole=.3,
        hovertemplate='%{label}: %{value:,.0f} NOK (%{percent})<extra></extra>'
    )])
    
    fig_expense_pie.update_layout(
        title='Current Monthly Expense Breakdown',
        height=400
    )
    
    st.plotly_chart(fig_expense_pie, use_container_width=True)
    
    # Show expense growth over time
    st.write("### Expense Growth Over Time")
    
    fig_expense_growth = go.Figure()
    
    # Add mortgage as the first expense category
    fig_expense_growth.add_trace(
        go.Bar(
            x=df['Year'],
            y=df['Monthly_Mortgage'],
            name='Mortgage',
            hovertemplate='Year %{x}<br>Mortgage: %{y:,.0f} NOK<extra></extra>'
        )
    )
    
    # Add stacked bars for each expense category (excluding mortgage which we already added)
    for category in expense_categories[1:]:
        fig_expense_growth.add_trace(
            go.Bar(
                x=df['Year'],
                y=df[category],
                name=category,
                hovertemplate='Year %{x}<br>' + category + ': %{y:,.0f} NOK<extra></extra>'
            )
        )
    
    # Customize layout
    fig_expense_growth.update_layout(
        title='Monthly Expenses Growth Over Time',
        xaxis_title='Year',
        yaxis_title='NOK per Month',
        barmode='stack',
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig_expense_growth, use_container_width=True)
    
    # Show expense table
    st.write("### Monthly Expenses Data")
    
    # Create a copy of the DataFrame with a renamed column to match our categories
    expense_cols = ['Year']
    
    # Add Monthly_Mortgage as the first expense column but name it 'Mortgage'
    expense_df = df.select(['Year', 'Monthly_Mortgage'] + expense_categories[1:] + ['Monthly_Expenses'])
    
    # Rename the Monthly_Mortgage column to Mortgage to match our category name
    expense_df = expense_df.rename({'Monthly_Mortgage': 'Mortgage'})
    
    # Display the DataFrame
    st.dataframe(expense_df.with_columns([pl.col(col).round(0) for col in expense_df.columns if col != 'Year']))

with tabs[3]:
    # Mortgage visualizations
    st.write("### Mortgage Amortization")
    
    # Create mortgage visualization
    fig_mortgage = go.Figure()
    
    # Add remaining balance line
    fig_mortgage.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['Remaining_Balance'],
            name='Remaining Balance',
            line=dict(color='red', width=2),
            hovertemplate='Year %{x}<br>Balance: %{y:,.0f} NOK<extra></extra>'
        )
    )
    
    # Add principal and interest as stacked bars
    fig_mortgage.add_trace(
        go.Bar(
            x=df['Year'],
            y=df['Annual_Principal'],
            name='Principal Payment',
            marker_color='blue',
            hovertemplate='Year %{x}<br>Principal: %{y:,.0f} NOK<extra></extra>'
        )
    )
    
    fig_mortgage.add_trace(
        go.Bar(
            x=df['Year'],
            y=df['Annual_Interest'],
            name='Interest Payment',
            marker_color='orange',
            hovertemplate='Year %{x}<br>Interest: %{y:,.0f} NOK<extra></extra>'
        )
    )
    
    # Customize layout
    fig_mortgage.update_layout(
        title='Mortgage Amortization Schedule',
        xaxis_title='Year',
        yaxis_title='NOK',
        barmode='stack',
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig_mortgage, use_container_width=True)
    
    # Display mortgage data
    st.write("### Mortgage Payment Breakdown")
    
    mortgage_info_df = df.select([
        'Year',
        'Monthly_Mortgage',
        'Annual_Principal',
        'Annual_Interest',
        'Annual_Mortgage',
        'Remaining_Balance'
    ])
    
    st.dataframe(mortgage_info_df.with_columns([
        pl.col('Monthly_Mortgage').round(0),
        pl.col('Annual_Principal').round(0),
        pl.col('Annual_Interest').round(0),
        pl.col('Annual_Mortgage').round(0),
        pl.col('Remaining_Balance').round(0)
    ]))
    
    # Calculate total interest vs principal
    total_principal = df['Annual_Principal'].sum()
    total_interest = df['Annual_Interest'].sum()
    total_paid = total_principal + total_interest
    
    # Display mortgage summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric('Total Principal Paid', f'{total_principal:,.0f} NOK')
    
    with col2:
        st.metric('Total Interest Paid', f'{total_interest:,.0f} NOK')
    
    with col3:
        st.metric('Interest as % of Payments', f'{(total_interest/total_paid*100):.1f}%')

with tabs[4]:
    # Savings visualization
    st.write("### Monthly Savings Potential")
    
    fig_savings = go.Figure()
    
    # Add monthly savings potential
    fig_savings.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['Monthly_Savings'],
            name='Monthly Savings Potential',
            line=dict(color='green', width=2),
            hovertemplate='Year %{x}<br>Monthly Savings: %{y:,.0f} NOK<extra></extra>'
        )
    )
    
    # Add real monthly savings
    fig_savings.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['Real_Monthly_Savings'],
            name='Real Monthly Savings (Inflation Adjusted)',
            line=dict(color='green', width=2, dash='dash'),
            hovertemplate='Year %{x}<br>Real Monthly Savings: %{y:,.0f} NOK<extra></extra>'
        )
    )
    
    # Add horizontal line at 0
    fig_savings.add_hline(y=0, line_dash="dash", line_color="red")
    
    # Customize layout
    fig_savings.update_layout(
        title='Monthly Savings Potential Over Time',
        xaxis_title='Year',
        yaxis_title='NOK per Month',
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig_savings, use_container_width=True)
    
    # Cumulative savings visualization
    st.write("### Cumulative Savings Potential")
    st.write(f"With {savings_return_rate}% annual return on investments")

    fig_cumulative = go.Figure()

    # Add nominal cumulative savings
    fig_cumulative.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['Cumulative_Savings'],
            name='Nominal Cumulative Savings',
            fill='tozeroy',
            line=dict(color='darkgreen', width=2),
            hovertemplate='Year %{x}<br>Cumulative Savings: %{y:,.0f} NOK<extra></extra>'
        )
    )

    # Add real cumulative savings
    fig_cumulative.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['Real_Cumulative_Savings'],
            name='Real Cumulative Savings (Inflation Adjusted)',
            line=dict(color='darkgreen', width=2, dash='dash'),
            hovertemplate='Year %{x}<br>Real Cumulative Savings: %{y:,.0f} NOK<extra></extra>'
        )
    )

    # Customize layout
    fig_cumulative.update_layout(
        title='Cumulative Savings Potential Over 30 Years',
        xaxis_title='Year',
        yaxis_title='NOK',
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig_cumulative, use_container_width=True)
    
    # Create a visualization of compound interest effect
    st.write("### Impact of Compound Interest on Savings")

    # Calculate savings without compound interest for comparison
    simple_cumulative = []
    running_total = 0
    for annual_saving in df['Annual_Savings']:
        running_total += annual_saving
        simple_cumulative.append(running_total)

    fig_compound = go.Figure()

    # Add compound savings line
    fig_compound.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['Cumulative_Savings'],
            name=f'With {savings_return_rate}% Return',
            line=dict(color='darkgreen', width=2),
            hovertemplate='Year %{x}<br>With Returns: %{y:,.0f} NOK<extra></extra>'
        )
    )

    # Add simple savings line
    fig_compound.add_trace(
        go.Scatter(
            x=df['Year'],
            y=simple_cumulative,
            name='Without Investment Returns',
            line=dict(color='lightgreen', width=2, dash='dash'),
            hovertemplate='Year %{x}<br>Without Returns: %{y:,.0f} NOK<extra></extra>'
        )
    )

    # Add area representing the compound interest earned
    fig_compound.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['Cumulative_Savings'],
            name='Compound Interest Earned',
            fill='tonexty',
            mode='none',
            fillcolor='rgba(0, 100, 0, 0.2)',
            hoverinfo='skip'
        )
    )

    # Customize layout
    fig_compound.update_layout(
        title='Effect of Compound Interest on Savings',
        xaxis_title='Year',
        yaxis_title='NOK',
        hovermode='x unified',
        height=500
    )

    st.plotly_chart(fig_compound, use_container_width=True)

    # Savings rate visualization
    st.write("### Savings Rate")
    
    fig_savings_rate = go.Figure()
    
    # Calculate savings rate as percentage of net income
    savings_rate = [(df['Monthly_Savings'][i] / df['Net_Monthly'][i]) * 100 for i in range(len(df))]
    
    # Add savings rate line
    fig_savings_rate.add_trace(
        go.Scatter(
            x=df['Year'],
            y=savings_rate,
            name='Savings Rate',
            line=dict(color='purple', width=2),
            hovertemplate='Year %{x}<br>Savings Rate: %{y:.1f}%<extra></extra>'
        )
    )
    
    # Customize layout
    fig_savings_rate.update_layout(
        title='Savings Rate (% of Net Income)',
        xaxis_title='Year',
        yaxis_title='Percentage',
        hovermode='x unified',
        height=300
    )
    
    st.plotly_chart(fig_savings_rate, use_container_width=True)

with tabs[5]:
    # Inflation impact
    st.write("### Impact of Inflation Over Time")
    st.write(f"Assuming an annual inflation rate of {inflation_rate}% and cost of living increase of {cost_of_living_increase}%")
    
    # Create purchasing power visualization
    fig_ppower = go.Figure()
    
    # Add purchasing power line
    fig_ppower.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['Inflation_Factor'] * 100,
            name='Purchasing Power',
            line=dict(color='purple', width=2),
            hovertemplate='Year %{x}<br>Purchasing Power: %{y:.1f}%<extra></extra>'
        )
    )
    
    # Customize layout
    fig_ppower.update_layout(
        title='Decline in Purchasing Power Over 30 Years',
        xaxis_title='Year',
        yaxis_title='Purchasing Power (% of Year 1)',
        hovermode='x unified',
        height=400,
        yaxis=dict(range=[0, 100])
    )
    
    st.plotly_chart(fig_ppower, use_container_width=True)
    
    # Create inflation impact visualization
    fig_inflation = go.Figure()
    
    # Add nominal and real income
    fig_inflation.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['Net_Monthly'],
            name='Nominal Net Income',
            line=dict(color='blue', width=2),
            hovertemplate='Year %{x}<br>Nominal Income: %{y:,.0f} NOK<extra></extra>'
        )
    )
    
    fig_inflation.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['Real_Monthly_Income'],
            name='Real Net Income',
            line=dict(color='blue', width=2, dash='dash'),
            hovertemplate='Year %{x}<br>Real Income: %{y:,.0f} NOK<extra></extra>'
        )
    )
    
    # Add nominal and real expenses
    total_monthly_outflow = [df['Monthly_Expenses'][i] + df['Monthly_Mortgage'][i] for i in range(len(df))]
    total_real_monthly_outflow = [df['Real_Monthly_Expenses'][i] + df['Real_Monthly_Mortgage'][i] for i in range(len(df))]
    
    fig_inflation.add_trace(
        go.Scatter(
            x=df['Year'],
            y=total_monthly_outflow,
            name='Nominal Total Expenses',
            line=dict(color='red', width=2),
            hovertemplate='Year %{x}<br>Nominal Expenses: %{y:,.0f} NOK<extra></extra>'
        )
    )
    
    fig_inflation.add_trace(
        go.Scatter(
            x=df['Year'],
            y=total_real_monthly_outflow,
            name='Real Total Expenses',
            line=dict(color='red', width=2, dash='dash'),
            hovertemplate='Year %{x}<br>Real Expenses: %{y:,.0f} NOK<extra></extra>'
        )
    )
    
    # Customize layout
    fig_inflation.update_layout(
        title='Impact of Inflation on Income and Expenses',
        xaxis_title='Year',
        yaxis_title='NOK per Month',
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig_inflation, use_container_width=True)

# Summary metrics
st.subheader('Financial Summary')

# First row - Current situation (Year 1)
st.write("### Current Financial Situation (Year 1)")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        'Net Monthly Income', 
        f'{df["Net_Monthly"][0]:,.0f} NOK'
    )
    
with col2:
    st.metric(
        'Total Monthly Expenses', 
        f'{df["Monthly_Expenses"][0] + df["Monthly_Mortgage"][0]:,.0f} NOK',
        help='Includes both living expenses and mortgage payment'
    )
    
with col3:
    st.metric(
        'Monthly Savings Potential', 
        f'{df["Monthly_Savings"][0]:,.0f} NOK'
    )
    
with col4:
    savings_ratio = (df["Monthly_Savings"][0] / df["Net_Monthly"][0]) * 100
    st.metric(
        'Savings Rate', 
        f'{savings_ratio:.1f}%',
        help='Percentage of net income that can be saved'
    )

# Second row - End of period projection (Year 30)
st.write("### Financial Projection (Year 30)")
col1, col2, col3, col4 = st.columns(4)

with col1:
    nominal_end_income = df["Net_Monthly"].tail(1)[0]
    real_end_income = df["Real_Monthly_Income"].tail(1)[0]
    st.metric(
        'Net Monthly Income', 
        f'{nominal_end_income:,.0f} NOK',
        delta=f'Real: {real_end_income:,.0f} NOK'
    )
    
with col2:
    end_expenses = df["Monthly_Expenses"].tail(1)[0] + df["Monthly_Mortgage"].tail(1)[0]
    st.metric(
        'Total Monthly Expenses', 
        f'{end_expenses:,.0f} NOK'
    )
    
with col3:
    end_savings = df["Monthly_Savings"].tail(1)[0]
    real_end_savings = df["Real_Monthly_Savings"].tail(1)[0]
    st.metric(
        'Monthly Savings Potential', 
        f'{end_savings:,.0f} NOK',
        delta=f'Real: {real_end_savings:,.0f} NOK'
    )
    
with col4:
    end_power = df["Inflation_Factor"].tail(1)[0] * 100
    st.metric(
        'Purchasing Power', 
        f'{end_power:.1f}%',
        delta=f'-{100-end_power:.1f}%',
        delta_color='inverse'
    )

# Third row - Lifetime totals
st.write("### Lifetime Totals (30 Years)")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        'Total Net Income', 
        f'{df["Net_Salary"].sum():,.0f} NOK'
    )
    
with col2:
    st.metric(
        'Total Mortgage Payments', 
        f'{df["Annual_Mortgage"].sum():,.0f} NOK'
    )
    
with col3:
    st.metric(
        'Total Living Expenses', 
        f'{df["Annual_Expenses"].sum():,.0f} NOK'
    )
    
with col4:
    compound_gain = df["Cumulative_Savings"].tail(1)[0] - sum(df["Annual_Savings"])
    compound_percentage = (compound_gain / sum(df["Annual_Savings"])) * 100 if sum(df["Annual_Savings"]) > 0 else 0
    st.metric(
        'Total Potential Savings', 
        f'{df["Cumulative_Savings"].tail(1)[0]:,.0f} NOK',
        delta=f'+{compound_gain:,.0f} NOK from returns',
        help=f'Includes {compound_percentage:.1f}% gain from compound interest'
    ) 