import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go

def main():
    st.set_page_config(page_title="Zephara Xcel Home Financing Simulator", layout="wide")

    # Title
    st.title("Zephara Xcel Home Financing Simulator")

    # Sidebar Inputs
    st.sidebar.header("Input Parameters")
    property_price = st.sidebar.number_input("Property Price (INR)", value=10_000_000, step=100_000)
    customer_initial_contribution = st.sidebar.number_input("Customer's Initial Contribution (Down Payment) (INR)", value=2_000_000, step=100_000)
    annual_rental_yield = st.sidebar.number_input("Annual Rental Yield (%)", value=3.5, step=0.1) / 100  # Convert percentage to decimal
    zx_loan_tenure_years = st.sidebar.number_input("Zephara Xcel Loan Tenure (Years)", value=20, step=1)
    traditional_interest_rate = st.sidebar.number_input("Traditional Loan Interest Rate (%)", value=7.0, step=0.1) / 100  # Convert percentage to decimal
    traditional_loan_tenure_years = st.sidebar.number_input("Traditional Loan Tenure (Years)", value=20, step=1)

    # Validate Inputs
    if customer_initial_contribution >= property_price:
        st.error("Error: Customer's initial contribution must be less than the property price.")
        return
    if annual_rental_yield <= 0 or annual_rental_yield >= 1:
        st.error("Error: Annual rental yield must be between 0% and 100%.")
        return
    if zx_loan_tenure_years <= 0 or traditional_loan_tenure_years <= 0:
        st.error("Error: Loan tenure must be a positive number.")
        return

    # Calculate Loan Tenure in Months
    zx_loan_tenure_months = int(zx_loan_tenure_years * 12)
    traditional_loan_tenure_months = int(traditional_loan_tenure_years * 12)

    # Simulate Zephara Xcel Model
    zx_simulation_df, zx_metrics = zx_simulator(
        property_price,
        customer_initial_contribution,
        annual_rental_yield,
        zx_loan_tenure_months
    )

    # Simulate Traditional Loan Model
    traditional_principal_amount = property_price - customer_initial_contribution
    traditional_simulation_df, traditional_metrics = traditional_loan_simulator(
        traditional_principal_amount,
        traditional_interest_rate,
        traditional_loan_tenure_months
    )

    # Display Results
    st.header("Simulation Results")

    # Metrics Comparison
    st.subheader("Key Metrics Comparison")

    metrics_data = {
        'Metric': ['Monthly Payment', 'Total EMI Paid', 'Total Interest/Rental Paid', 'Total Principal/Buyback Paid', 'Total Payment', 'Bank Profit'],
        'Zephara Xcel Model (INR)': [
            zx_metrics['monthly_payment'],
            zx_metrics['total_emi_paid'],
            zx_metrics['total_rental_income'],
            zx_metrics['total_buyback_amount'],
            zx_metrics['total_emi_paid'],
            zx_metrics['bank_profit']
        ],
        'Traditional Loan Model (INR)': [
            traditional_metrics['monthly_payment'],
            traditional_metrics['total_emi_paid'],
            traditional_metrics['total_interest_paid'],
            traditional_metrics['total_principal_paid'],
            traditional_metrics['total_emi_paid'],
            traditional_metrics['bank_profit']
        ]
    }

    metrics_df = pd.DataFrame(metrics_data)

    st.table(metrics_df.style.format({"Zephara Xcel Model (INR)": "{:,.2f}", "Traditional Loan Model (INR)": "{:,.2f}"}))

    # Savings Calculation
    total_savings = traditional_metrics['total_emi_paid'] - zx_metrics['total_emi_paid']
    st.markdown(f"**Total Savings with Zephara Xcel Model:** INR {total_savings:,.2f}")

    # Graphs Side by Side
    st.subheader("Ownership Transition Over Time")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Zephara Xcel Model**")
        fig1 = plot_ownership_transition(zx_simulation_df, 'ZX')
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown("**Traditional Loan Model**")
        fig2 = plot_outstanding_balance(traditional_simulation_df)
        st.plotly_chart(fig2, use_container_width=True)

    # EMI Breakdown
    st.subheader("EMI Breakdown Over Time")

    fig3 = plot_emi_breakdown(zx_simulation_df, traditional_simulation_df)
    st.plotly_chart(fig3, use_container_width=True)

    # Detailed Tables
    st.subheader("Detailed Simulation Data")
    with st.expander("Zephara Xcel Model Data"):
        st.dataframe(zx_simulation_df.style.format("{:,.2f}"))

    with st.expander("Traditional Loan Model Data"):
        st.dataframe(traditional_simulation_df.style.format("{:,.2f}"))

    # Option to Download Data
    st.subheader("Download Simulation Data")
    download_data(zx_simulation_df, traditional_simulation_df)

def zx_simulator(property_price, customer_initial_contribution, annual_rental_yield, loan_tenure_months):
    # Initial Calculations
    nbfc_initial_contribution = property_price - customer_initial_contribution
    monthly_rental_rate = annual_rental_yield / 12
    T = loan_tenure_months
    r = monthly_rental_rate

    # Calculate EMI
    EMI = (nbfc_initial_contribution * r * (1 + r)**T) / ((1 + r)**T - 1)

    # Initialize lists to store simulation data
    months = []
    emi_list = []
    rental_income_list = []
    buyback_amount_list = []
    nbfc_share_percentage_list = []
    customer_share_percentage_list = []
    nbfc_share_value_list = []
    customer_share_value_list = []

    # Initial shares
    nbfc_share_value = nbfc_initial_contribution
    customer_share_value = customer_initial_contribution

    # Simulation Loop
    for n in range(1, T + 1):
        rental_income = nbfc_share_value * r
        buyback_amount = EMI - rental_income
        nbfc_share_value -= buyback_amount
        customer_share_value += buyback_amount

        # Store data
        months.append(n)
        emi_list.append(EMI)
        rental_income_list.append(rental_income)
        buyback_amount_list.append(buyback_amount)
        nbfc_share_percentage_list.append(nbfc_share_value / property_price * 100)  # Percentage
        customer_share_percentage_list.append(customer_share_value / property_price * 100)  # Percentage
        nbfc_share_value_list.append(nbfc_share_value)
        customer_share_value_list.append(customer_share_value)

    # Create DataFrame
    simulation_df = pd.DataFrame({
        'Month': months,
        'EMI (INR)': emi_list,
        'Rental Income (INR)': rental_income_list,
        'Buyback Amount (INR)': buyback_amount_list,
        'NBFC Ownership (%)': nbfc_share_percentage_list,
        'Customer Ownership (%)': customer_share_percentage_list,
        'NBFC Share Value (INR)': nbfc_share_value_list,
        'Customer Share Value (INR)': customer_share_value_list
    })

    # Calculate Metrics
    total_emi_paid = simulation_df['EMI (INR)'].sum()
    total_rental_income = simulation_df['Rental Income (INR)'].sum()
    total_buyback_amount = simulation_df['Buyback Amount (INR)'].sum()
    bank_profit = total_rental_income  # In ZX model, bank profit is the rental income

    metrics = {
        'monthly_payment': EMI,
        'total_emi_paid': total_emi_paid,
        'total_rental_income': total_rental_income,
        'total_buyback_amount': total_buyback_amount,
        'bank_profit': bank_profit
    }

    return simulation_df, metrics

def traditional_loan_simulator(principal_amount, annual_interest_rate, loan_tenure_months):
    # Calculate monthly interest rate
    r = annual_interest_rate / 12
    T = loan_tenure_months

    # Calculate EMI
    EMI = (principal_amount * r * (1 + r)**T) / ((1 + r)**T - 1)

    # Initialize lists to store simulation data
    months = []
    emi_list = []
    interest_paid_list = []
    principal_paid_list = []
    outstanding_balance_list = []

    # Initial outstanding balance
    outstanding_balance = principal_amount

    # Simulation Loop
    for n in range(1, T + 1):
        interest_payment = outstanding_balance * r
        principal_payment = EMI - interest_payment
        outstanding_balance -= principal_payment

        # Store data
        months.append(n)
        emi_list.append(EMI)
        interest_paid_list.append(interest_payment)
        principal_paid_list.append(principal_payment)
        outstanding_balance_list.append(outstanding_balance)

    # Create DataFrame
    simulation_df = pd.DataFrame({
        'Month': months,
        'EMI (INR)': emi_list,
        'Interest Paid (INR)': interest_paid_list,
        'Principal Paid (INR)': principal_paid_list,
        'Outstanding Balance (INR)': outstanding_balance_list
    })

    # Calculate Metrics
    total_emi_paid = simulation_df['EMI (INR)'].sum()
    total_interest_paid = simulation_df['Interest Paid (INR)'].sum()
    total_principal_paid = simulation_df['Principal Paid (INR)'].sum()
    bank_profit = total_interest_paid  # In traditional loan, bank profit is the interest paid

    metrics = {
        'monthly_payment': EMI,
        'total_emi_paid': total_emi_paid,
        'total_interest_paid': total_interest_paid,
        'total_principal_paid': total_principal_paid,
        'bank_profit': bank_profit
    }

    return simulation_df, metrics

def plot_ownership_transition(simulation_df, model_type):
    fig = go.Figure()
    if model_type == 'ZX':
        fig.add_trace(go.Scatter(
            x=simulation_df['Month'],
            y=simulation_df['NBFC Ownership (%)'],
            mode='lines',
            name='NBFC Ownership (%)'
        ))
        fig.add_trace(go.Scatter(
            x=simulation_df['Month'],
            y=simulation_df['Customer Ownership (%)'],
            mode='lines',
            name='Customer Ownership (%)'
        ))
        fig.update_layout(
            title='Ownership Transition Over Time',
            xaxis_title='Month',
            yaxis_title='Ownership Percentage',
            legend_title='Legend'
        )
    return fig

def plot_outstanding_balance(simulation_df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=simulation_df['Month'],
        y=simulation_df['Outstanding Balance (INR)'],
        mode='lines',
        name='Outstanding Balance (INR)'
    ))
    fig.update_layout(
        title='Outstanding Balance Over Time',
        xaxis_title='Month',
        yaxis_title='Outstanding Balance (INR)',
        legend_title='Legend'
    )
    return fig

def plot_emi_breakdown(zx_df, traditional_df):
    fig = go.Figure()

    # ZX Model
    fig.add_trace(go.Scatter(
        x=zx_df['Month'],
        y=zx_df['Rental Income (INR)'],
        mode='lines',
        name='ZX Rental Income'
    ))
    fig.add_trace(go.Scatter(
        x=zx_df['Month'],
        y=zx_df['Buyback Amount (INR)'],
        mode='lines',
        name='ZX Buyback Amount'
    ))

    # Traditional Loan Model
    fig.add_trace(go.Scatter(
        x=traditional_df['Month'],
        y=traditional_df['Interest Paid (INR)'],
        mode='lines',
        name='Traditional Interest Paid'
    ))
    fig.add_trace(go.Scatter(
        x=traditional_df['Month'],
        y=traditional_df['Principal Paid (INR)'],
        mode='lines',
        name='Traditional Principal Paid'
    ))

    fig.update_layout(
        title='EMI Breakdown Over Time',
        xaxis_title='Month',
        yaxis_title='Amount (INR)',
        legend_title='Legend'
    )
    return fig

def download_data(zx_df, traditional_df):
    # Combine data into Excel file
    with pd.ExcelWriter("simulation_data.xlsx") as writer:
        zx_df.to_excel(writer, sheet_name='Zephara Xcel Model', index=False)
        traditional_df.to_excel(writer, sheet_name='Traditional Loan Model', index=False)
    with open("simulation_data.xlsx", "rb") as file:
        btn = st.download_button(
            label="Download Simulation Data",
            data=file,
            file_name="simulation_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == '__main__':
    main()

