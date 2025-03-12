import polars as pl

def calculate_norwegian_tax(income, wealth, loans=0, mortgage=0, year=2025, primary_home_value=0, bank_balance=0, income_type='wage', 
                            mortgage_interest_rate=0.04, other_loans_interest_rate=0.06):
    """
    Calculate Norwegian taxes based on income and wealth, accounting for loans and mortgages.
    
    Parameters:
    -----------
    income : float
        Personal income in NOK
    wealth : float
        Gross wealth in NOK (before subtracting loans/mortgage)
    loans : float, optional
        Total non-mortgage loans in NOK (default: 0)
    mortgage : float, optional
        Mortgage debt in NOK (default: 0)
    year : int, optional
        Tax year (default: 2025)
    primary_home_value : float, optional
        Value of primary residence in NOK, used for wealth tax calculations (default: 0)
    bank_balance : float, optional
        Cash in bank accounts in NOK (default: 0)
    income_type : str, optional
        Type of income: 'wage', 'self_employment', or 'pension' (default: 'wage')
    mortgage_interest_rate : float, optional
        Annual interest rate on mortgage as a decimal (default: 0.04 which is 4%)
    other_loans_interest_rate : float, optional
        Annual interest rate on other loans as a decimal (default: 0.06 which is 6%)
        
    Returns:
    --------
    dict
        Dictionary containing tax details
    """
    # Validate inputs
    if income < 0:
        raise ValueError('Income cannot be negative')
    if wealth < 0:
        raise ValueError('Wealth cannot be negative')
    if loans < 0:
        raise ValueError('Loans cannot be negative')
    if mortgage < 0:
        raise ValueError('Mortgage cannot be negative')
    if primary_home_value < 0:
        raise ValueError('Primary home value cannot be negative')
    if bank_balance < 0:
        raise ValueError('Bank balance cannot be negative')
    
    if year not in [2024, 2025]:
        raise ValueError(f'Tax calculations for year {year} are not supported. Use 2024 or 2025.')
    
    if income_type not in ['wage', 'self_employment', 'pension']:
        raise ValueError(f'Income type {income_type} is not supported. Use "wage", "self_employment", or "pension".')
    
    result = {
        'income': income,
        'gross_wealth': wealth,
        'loans': loans,
        'mortgage': mortgage,
        'primary_home_value': primary_home_value,
        'bank_balance': bank_balance,
        'income_type': income_type,
        'year': year,
        'tax_components': {}
    }
    
    # Income tax parameters
    if year == 2025:
        # Tax on ordinary income (alminnelig inntekt)
        income_tax_rate = 0.22  # 22% flat rate

        # Personal deduction (personfradrag)
        personal_deduction = 79_200  # NOK
        
        # Social security contribution (trygdeavgift)
        social_security_rates = {
            'wage': 0.080,            # 8.0% for wage income
            'self_employment': 0.112, # 11.2% for self-employment income
            'pension': 0.051          # 5.1% for pension income
        }
        
        # Bracket tax (trinnskatt) thresholds and rates - corrected from regjeringen.no
        bracket_tax_thresholds = [
            (0, 0),
            (217_400, 0.017),  # 1.7% - Trinn 1
            (306_050, 0.040),  # 4.0% - Trinn 2 
            (697_150, 0.137),  # 13.7% - Trinn 3
            (942_400, 0.167),  # 16.7% - Trinn 4
            (1_410_750, 0.177), # 17.7% - Trinn 5
        ]
        
        # Wealth tax (formuesskatt) parameters - corrected from regjeringen.no
        # Wealth tax threshold
        wealth_tax_threshold = 1_760_000  # NOK
        
        # Municipal wealth tax
        municipal_wealth_tax_rate = 0.007  # 0.7%
        
        # State wealth tax
        state_wealth_tax_thresholds = [
            (1_760_000, 0.00525),  # 0.525% for wealth above 1,760,000
            (20_070_000, 0.01),    # Additional 1.0% for wealth above 20,070,000
        ]
        
        # Primary home value reduction
        primary_home_value_reduction = 0.25  # Primary homes are valued at 25% of market value
        
        # Secondary homes value reduction
        secondary_home_value_reduction = 0.95  # Secondary homes are valued at 95% of market value
        
        # Interest deduction rate on ordinary income
        interest_deduction_rate = 0.22  # 22% tax deduction on interest paid
    
    elif year == 2024:
        # Tax on ordinary income (alminnelig inntekt)
        income_tax_rate = 0.22  # 22% flat rate

        # Personal deduction (personfradrag)
        personal_deduction = 77_700  # NOK
        
        # Social security contribution (trygdeavgift)
        social_security_rates = {
            'wage': 0.080,            # 8.0% for wage income
            'self_employment': 0.112, # 11.2% for self-employment income
            'pension': 0.051          # 5.1% for pension income
        }
        
        # Bracket tax (trinnskatt) thresholds and rates - verified from regjeringen.no
        bracket_tax_thresholds = [
            (0, 0),
            (208_050, 0.017),  # 1.7% tax for income above 208,050
            (293_250, 0.040),  # 4.0% tax for income above 293,250
            (667_650, 0.137),  # 13.7% tax for income above 667,650
            (902_300, 0.167),  # 16.7% tax for income above 902,300
            (1_350_000, 0.177), # 17.7% tax for income above 1,350,000
        ]
        
        # Wealth tax (formuesskatt) parameters - verified from regjeringen.no
        # Wealth tax threshold
        wealth_tax_threshold = 1_700_000  # NOK
        
        # Municipal wealth tax
        municipal_wealth_tax_rate = 0.007  # 0.7%
        
        # State wealth tax
        state_wealth_tax_thresholds = [
            (1_700_000, 0.00525),  # 0.525% for wealth above 1,700,000
            (19_970_000, 0.01),    # Additional 1.0% for wealth above 19,970,000
        ]
        
        # Primary home value reduction
        primary_home_value_reduction = 0.25  # Primary homes are valued at 25% of market value
        
        # Secondary homes value reduction
        secondary_home_value_reduction = 0.95  # Secondary homes are valued at 95% of market value
        
        # Interest deduction rate on ordinary income
        interest_deduction_rate = 0.22  # 22% tax deduction on interest paid

    # Calculate total debt
    total_debt = loans + mortgage
    result['total_debt'] = total_debt
    
    # Calculate the taxable value of the primary home
    taxable_primary_home_value = 0
    if primary_home_value > 0:
        # For primary homes, only a portion of the value is taxable
        # Different rates for value above 10 million
        if primary_home_value <= 10_000_000:
            taxable_primary_home_value = primary_home_value * primary_home_value_reduction
        else:
            # 25% for first 10 million, 50% for amount above 10 million
            taxable_primary_home_value = (10_000_000 * primary_home_value_reduction) + ((primary_home_value - 10_000_000) * 0.5)
    
    # Calculate net wealth for tax purposes
    # Wealth - debt (all debts reduce taxable wealth)
    net_wealth_for_tax = max(0, wealth - total_debt)
    result['net_wealth_for_tax'] = net_wealth_for_tax
    
    # Calculate interest expense (based on provided rates)
    mortgage_interest = mortgage * mortgage_interest_rate
    other_loans_interest = loans * other_loans_interest_rate
    total_interest = mortgage_interest + other_loans_interest
    
    # Store interest calculations in result
    result['interest'] = {
        'mortgage_interest_rate': mortgage_interest_rate,
        'other_loans_interest_rate': other_loans_interest_rate,
        'mortgage_interest': mortgage_interest,
        'other_loans_interest': other_loans_interest,
        'total_interest': total_interest
    }
    
    # Calculate interest deduction (tax savings from interest expenses)
    interest_deduction = total_interest * interest_deduction_rate
    result['tax_components']['interest_deduction'] = -interest_deduction  # Negative as it reduces tax
    
    # Calculate social security contribution (trygdeavgift)
    social_security_rate = social_security_rates[income_type]
    social_security = income * social_security_rate
    result['tax_components']['social_security'] = social_security
    
    # Calculate income tax (skatt på alminnelig inntekt)
    # Interest payments are deductible from ordinary income
    taxable_income = max(0, income - personal_deduction - total_interest)
    income_tax = taxable_income * income_tax_rate
    result['tax_components']['income_tax'] = income_tax
    
    # Calculate bracket tax (trinnskatt)
    # Bracket tax is not affected by interest deductions
    bracket_tax = 0
    remaining_income = income  # Use a copy so we don't modify the original
    
    for i in range(len(bracket_tax_thresholds) - 1, 0, -1):
        threshold, rate = bracket_tax_thresholds[i]
        if remaining_income > threshold:
            bracket_tax += (remaining_income - threshold) * rate
            remaining_income = threshold
    
    result['tax_components']['bracket_tax'] = bracket_tax
    
    # Calculate wealth tax (formuesskatt)
    # Wealth tax is calculated on net wealth (assets minus liabilities)
    
    # Municipal wealth tax - 0.7% on net wealth above threshold
    municipal_wealth_tax = max(0, (net_wealth_for_tax - wealth_tax_threshold) * municipal_wealth_tax_rate)
    result['tax_components']['municipal_wealth_tax'] = municipal_wealth_tax
    
    # State wealth tax - progressive
    state_wealth_tax = 0
    remaining_wealth = net_wealth_for_tax  # Use a copy so we don't modify the original
    
    for i in range(len(state_wealth_tax_thresholds) - 1, -1, -1):
        threshold, rate = state_wealth_tax_thresholds[i]
        if remaining_wealth > threshold:
            state_wealth_tax += (remaining_wealth - threshold) * rate
            remaining_wealth = threshold
    
    result['tax_components']['state_wealth_tax'] = state_wealth_tax
    
    # Calculate total tax
    total_tax = sum(result['tax_components'].values())
    result['total_tax'] = total_tax
    
    # Calculate effective tax rate
    if result['income'] > 0:
        result['effective_tax_rate'] = total_tax / result['income']
    else:
        result['effective_tax_rate'] = 0
        
    return result


def tax_simulation(income_range, wealth_range, loans=0, mortgage=0, bank_balance=0, year=2025, income_type='wage',
                  mortgage_interest_rate=0.04, other_loans_interest_rate=0.06):
    """
    Simulate taxes for a range of incomes and wealth levels, accounting for loans and mortgages.
    
    Parameters:
    -----------
    income_range : list or tuple
        (min_income, max_income, step)
    wealth_range : list or tuple
        (min_wealth, max_wealth, step)
    loans : float, optional
        Total non-mortgage loans in NOK (default: 0)
    mortgage : float, optional
        Mortgage debt in NOK (default: 0)
    bank_balance : float, optional
        Cash in bank accounts in NOK (default: 0)
    year : int, optional
        Tax year (default: 2025)
    income_type : str, optional
        Type of income: 'wage', 'self_employment', or 'pension' (default: 'wage')
    mortgage_interest_rate : float, optional
        Annual interest rate on mortgage as a decimal (default: 0.04 which is 4%)
    other_loans_interest_rate : float, optional
        Annual interest rate on other loans as a decimal (default: 0.06 which is 6%)
        
    Returns:
    --------
    polars.DataFrame
        DataFrame with tax calculations for each income and wealth combination
    """
    min_income, max_income, income_step = income_range
    min_wealth, max_wealth, wealth_step = wealth_range
    
    income_values = range(min_income, max_income + 1, income_step)
    wealth_values = range(min_wealth, max_wealth + 1, wealth_step)
    
    results = []
    
    for income in income_values:
        for wealth in wealth_values:
            tax_result = calculate_norwegian_tax(
                income=income, 
                wealth=wealth, 
                loans=loans, 
                mortgage=mortgage, 
                bank_balance=bank_balance,
                year=year, 
                income_type=income_type,
                mortgage_interest_rate=mortgage_interest_rate,
                other_loans_interest_rate=other_loans_interest_rate
            )
            results.append({
                'income': income,
                'gross_wealth': wealth,
                'net_wealth': wealth - loans - mortgage,
                'bank_balance': bank_balance,
                'loans': loans,
                'mortgage': mortgage,
                'total_interest': tax_result['interest']['total_interest'],
                'total_tax': tax_result['total_tax'],
                'effective_tax_rate': tax_result['effective_tax_rate'],
                'income_tax': tax_result['tax_components'].get('income_tax', 0),
                'bracket_tax': tax_result['tax_components'].get('bracket_tax', 0),
                'social_security': tax_result['tax_components'].get('social_security', 0),
                'interest_deduction': tax_result['tax_components'].get('interest_deduction', 0),
                'municipal_wealth_tax': tax_result['tax_components'].get('municipal_wealth_tax', 0),
                'state_wealth_tax': tax_result['tax_components'].get('state_wealth_tax', 0),
            })
    
    return pl.DataFrame(results)


def mortgage_impact_analysis(income, wealth, mortgage_values, bank_balance=0, year=2025, income_type='wage',
                           mortgage_interest_rate=0.04, other_loans_interest_rate=0.06):
    """
    Analyze the impact of different mortgage levels on tax liability.
    
    Parameters:
    -----------
    income : float
        Personal income in NOK
    wealth : float
        Gross wealth in NOK
    mortgage_values : list
        List of mortgage amounts to analyze
    bank_balance : float, optional
        Cash in bank accounts in NOK (default: 0)
    year : int, optional
        Tax year (default: 2025)
    income_type : str, optional
        Type of income: 'wage', 'self_employment', or 'pension' (default: 'wage')
    mortgage_interest_rate : float, optional
        Annual interest rate on mortgage as a decimal (default: 0.04 which is 4%)
    other_loans_interest_rate : float, optional
        Annual interest rate on other loans as a decimal (default: 0.06 which is 6%)
        
    Returns:
    --------
    polars.DataFrame
        DataFrame showing tax implications of different mortgage levels
    """
    results = []
    
    for mortgage in mortgage_values:
        tax_result = calculate_norwegian_tax(
            income=income, 
            wealth=wealth, 
            mortgage=mortgage, 
            bank_balance=bank_balance,
            year=year, 
            income_type=income_type,
            mortgage_interest_rate=mortgage_interest_rate,
            other_loans_interest_rate=other_loans_interest_rate
        )
        results.append({
            'income': income,
            'gross_wealth': wealth,
            'mortgage': mortgage,
            'net_wealth': wealth - mortgage,
            'bank_balance': bank_balance,
            'mortgage_interest': tax_result['interest']['mortgage_interest'],
            'total_interest': tax_result['interest']['total_interest'],
            'total_tax': tax_result['total_tax'],
            'effective_tax_rate': tax_result['effective_tax_rate'],
            'income_tax': tax_result['tax_components'].get('income_tax', 0),
            'bracket_tax': tax_result['tax_components'].get('bracket_tax', 0),
            'social_security': tax_result['tax_components'].get('social_security', 0),
            'interest_deduction': tax_result['tax_components'].get('interest_deduction', 0),
            'municipal_wealth_tax': tax_result['tax_components'].get('municipal_wealth_tax', 0),
            'state_wealth_tax': tax_result['tax_components'].get('state_wealth_tax', 0),
        })
    
    return pl.DataFrame(results)


