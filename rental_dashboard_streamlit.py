import pandas as pd
import streamlit as st
from datetime import datetime
import numpy as np

st.set_page_config(layout="wide")
st.title("🏠 Rental Payment Dashboard")

# Load or generate data (simulate loading Excel data)
@st.cache_data
def load_data():
    df = pd.read_csv("tenant_payments.csv", parse_dates=['Due Date', 'Payment Date'])
    return df

# Status coloring function
def color_status(status):
    color_map = {
        'Paid': 'green',
        'Partial': 'orange',
        'Unpaid': 'red',
        'Overdue': 'darkred'
    }
    return f"color: {color_map.get(status, 'black')}"

df = load_data()

# Filter section
st.sidebar.header("🔍 Filters")
tenant_filter = st.sidebar.selectbox("Select Tenant", options=['All'] + sorted(df['Tenant Name'].unique().tolist()))

if tenant_filter != 'All':
    df = df[df['Tenant Name'] == tenant_filter]

# Summary
st.subheader("📊 Summary Table")
summary = df.groupby(['Tenant Name', 'Unit']).agg(
    Remaining_Balance=('Remaining', 'sum'),
    Next_Due_Date=('Due Date', lambda x: x[x >= pd.Timestamp.today()].min()),
    Last_Status=('Status', lambda x: x.iloc[-1])
).reset_index()

summary['Next_Due_Date'] = pd.to_datetime(summary['Next_Due_Date']).dt.date

def highlight_due_date(val):
    if pd.isnull(val):
        return ''
    elif val < datetime.today().date():
        return 'background-color: red'
    elif val <= datetime.today().date() + pd.Timedelta(days=7):
        return 'background-color: yellow'
    return ''

st.dataframe(summary.style.applymap(
    highlight_due_date,
    subset=['Next_Due_Date']
))

# Detailed payments
st.subheader("📋 Payment Records")
df['Due Date'] = df['Due Date'].dt.date
st.dataframe(df.style.applymap(color_status, subset=['Status']))

# Add payment
st.sidebar.header("➕ Add Payment")
with st.sidebar.form("new_payment"):
    unit = st.selectbox("Unit", options=df['Unit'].unique())
    tenant_name = df[df['Unit'] == unit]['Tenant Name'].iloc[0]
    installment = st.number_input("Installment Number", min_value=1, step=1)
    due_date = st.date_input("Due Date")
    amount_due = st.number_input("Amount Due", min_value=0.0, step=100.0)
    amount_paid = st.number_input("Amount Paid", min_value=0.0, step=100.0)
    payment_date = st.date_input("Payment Date")
    method = st.selectbox("Payment Method", ['Bank Transfer', 'Cash', 'Cheque'])

    submitted = st.form_submit_button("Add Payment")
    if submitted:
        remaining = amount_due - amount_paid
        if amount_paid == amount_due:
            status = 'Paid'
        elif amount_paid == 0:
            status = 'Unpaid'
        elif payment_date > due_date:
            status = 'Overdue'
        else:
            status = 'Partial'

        new_row = pd.DataFrame([{
            'Unit': unit,
            'Tenant Name': tenant_name,
            'Installment': installment,
            'Due Date': due_date,
            'Amount Due': amount_due,
            'Amount Paid': amount_paid,
            'Payment Date': payment_date,
            'Method': method,
            'Remaining': remaining,
            'Status': status
        }])

        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv("tenant_payments.csv", index=False)
        st.success("Payment added successfully!")
