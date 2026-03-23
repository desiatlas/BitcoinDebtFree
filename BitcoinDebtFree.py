import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy_financial as npf
import yfinance as yf

st.set_page_config(page_title="Debt Slayer & Sats Stacker", layout="wide")

# ────────────────────────────────────────────────
# Home Loan Tracker Tab
# ────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🏛️ Loan Tracker",
    "₿ BTC Stacker",
    "₹ Expenses & Savings"
])
with tab1:
    st.title("Loan Payoff Calculator & Tracker")
    # st.markdown("")

    col1, col2 = st.columns(2)

    with col1:
        principal = st.number_input(
            "Current Loan Balance (₹)",
            min_value=0,
            value=100000,
            step=1000,
            help="Your outstanding principal right now"
        )
        annual_rate = st.number_input(
            "Annual Interest Rate (%)",
            min_value=0.0,
            value=7.4,
            step=0.1,
            help="Floating or fixed — use current effective rate"
        ) / 100
        start_date = st.date_input(
            "Tracking Start Date",
            value=datetime.today().date(),  # defaults to today
            help="Usually today, or the date of your last statement"
        )

    with col2:
        fixed_emi = 61742.0 
       # st.markdown(f"**)")
        extra_per_year = st.number_input(
            "Extra Payment per Year (₹)",
            min_value=0.0,
            value=0.0,
            step=50000.0,
            format="%.0f",
            help="Additional lump sum you plan to pay once every year (applied on anniversary)"
        )
        show_without_extra = st.checkbox("Compare with NO extra payments", value=True)

    monthly_rate = annual_rate / 12

    # Calculate remaining months with fixed EMI (without yearly extra)
    remaining_months = 0
    if principal > 0 and monthly_rate > 0 and fixed_emi > monthly_rate * principal:
        remaining_months = npf.nper(monthly_rate, -fixed_emi, principal)
        remaining_months = max(remaining_months, 0)
        remaining_years = remaining_months / 12
        st.markdown(f"**Computed remaining term at current rate (no extra)**: ≈ {remaining_months:.0f} months ({remaining_years:.1f} years)")
        #st.info("**")
    else:
        st.warning("EMI too low for current principal & rate — loan won't be paid off.")

    # ────────────────────────────────────────────────
    # Payoff simulation function (with yearly extra)
    # ────────────────────────────────────────────────
    def calculate_payoff(balance, monthly_rate, fixed_payment, extra_yearly=0):
        total_monthly = fixed_payment
        current_balance = balance
        current_date = start_date
        total_interest = 0
        months = 0
        schedule = []
        next_extra_date = start_date + timedelta(days=365)  # first extra after 1 year

        while current_balance > 0 and months < 600:
            interest_this_month = current_balance * monthly_rate

            # Apply yearly extra if date matches
            payment_this_month = total_monthly
            extra_this_month = 0
            if current_date >= next_extra_date and extra_yearly > 0:
                extra_this_month = extra_yearly
                payment_this_month += extra_this_month
                next_extra_date += timedelta(days=365)  # next year

            if payment_this_month > current_balance + interest_this_month:
                payment_this_month = current_balance + interest_this_month

            principal_this_month = payment_this_month - interest_this_month
            current_balance -= principal_this_month
            total_interest += interest_this_month

            schedule.append({
                'Month': months + 1,
                'Date': current_date,
                'Beginning Balance': round(current_balance + principal_this_month, 2),
                'Payment': round(payment_this_month, 2),
                'Interest': round(interest_this_month, 2),
                'Principal': round(principal_this_month, 2),
                'Extra Yearly': round(extra_this_month, 2) if extra_this_month > 0 else 0,
                'Ending Balance': max(round(current_balance, 2), 0)
            })

            current_date += timedelta(days=30)
            months += 1

            if current_balance <= 0:
                break

        df = pd.DataFrame(schedule)
        payoff_date = current_date - timedelta(days=30) if current_balance <= 0 else None
        return df, payoff_date, total_interest, months, None

    # Run scenarios
    df_extra, payoff_extra, interest_extra, months_extra, error_msg = calculate_payoff(
        principal, monthly_rate, fixed_emi, extra_yearly=extra_per_year
    )

    df_noextra, payoff_noextra, interest_noextra, months_noextra, _ = None, None, None, None, None
    if show_without_extra:
        df_noextra, payoff_noextra, interest_noextra, months_noextra, _ = calculate_payoff(
            principal, monthly_rate, fixed_emi, extra_yearly=0
        )

    # ── Display results ──────────────────────────────────────────
    if error_msg:
        st.error(error_msg)
    elif df_extra is not None:
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.subheader("Payoff Timeline")

            if payoff_extra:
                months_str = f"{months_extra} months"
                if months_extra >= 12:
                    years = months_extra // 12
                    rem_months = months_extra % 12
                    months_str = f"≈ {years} years {rem_months} months"

                st.success(f"**Debt-free on ≈ {payoff_extra.strftime('%d %b %Y')}**  ({months_str})")

                if months_noextra is not None:
                    saved_months = months_noextra - months_extra
                    if saved_months > 3:
                        saved_years = saved_months / 12
                        st.markdown(f"→ **You save ≈ {saved_years:.1f} years** by paying ₹{extra_per_year:,} extra per year! 🚀")

        with col_right:
            st.subheader("Key Numbers")
            st.metric("Total Interest (with yearly extra)", f"₹{interest_extra:,.0f}")

            if interest_noextra is not None:
                saved_interest = interest_noextra - interest_extra
                if saved_interest > 10000:
                    st.metric("Interest Saved", f"₹{saved_interest:,.0f}", delta=f"₹{saved_interest:,.0f}", delta_color="normal")

        # Interest vs Principal pie chart
        if not df_extra.empty:
            total_interest_paid = df_extra['Interest'].sum()
            total_principal_paid = df_extra['Principal'].sum()
            fig_pie, ax_pie = plt.subplots(figsize=(6, 6))
            ax_pie.pie([total_interest_paid, total_principal_paid], labels=['Interest', 'Principal'], autopct='%1.1f%%', colors=['#ff9999','#66b3ff'])
            ax_pie.set_title("Interest vs Principal Breakdown")
            st.pyplot(fig_pie)

        # Balance chart
        st.subheader("Loan Balance Over Time")
        fig, ax = plt.subplots(figsize=(10, 5.5))

        if df_noextra is not None and show_without_extra:
            ax.plot(df_noextra['Date'], df_noextra['Ending Balance'],
                    label="No extra", color='gray', linestyle='--', linewidth=2)

        ax.plot(df_extra['Date'], df_extra['Ending Balance'],
                label=f"With ₹{extra_per_year:,} extra/year", color='#d62728', linewidth=3)

        ax.set_xlabel("Date")
        ax.set_ylabel("Remaining Balance (₹)")
        ax.grid(True, alpha=0.3)
        ax.legend()
        plt.tight_layout()
        st.pyplot(fig)

        with st.expander("View full month-by-month schedule"):
            st.dataframe(
                df_extra.style.format({
                    'Beginning Balance': '₹{:,.2f}',
                    'Payment': '₹{:,.2f}',
                    'Interest': '₹{:,.2f}',
                    'Principal': '₹{:,.2f}',
                    'Ending Balance': '₹{:,.2f}',
                    'Extra Yearly': '₹{:,.2f}'
                }),
                use_container_width=True
            )

            if not df_extra.empty:
                total_principal = df_extra['Principal'].sum()
                total_interest = df_extra['Interest'].sum()
                grand_total = total_principal + total_interest

                st.markdown("### Grand Totals (Entire Payoff Period)")
                col_t1, col_t2, col_t3 = st.columns(3)
                col_t1.metric("Total Principal Paid", f"₹{total_principal:,.0f}")
                col_t2.metric("Total Interest Paid", f"₹{total_interest:,.0f}")
                col_t3.metric("Grand Total Paid", f"₹{grand_total:,.0f}")

    else:
        st.info("Enter loan details above to see when you'll be debt-free ✨")

    st.markdown("---")
    st.caption("30-day month approximation • Not financial advice")

# ────────────────────────────────────────────────
# BTC Stacker Tab (unchanged)
# ────────────────────────────────────────────────

with tab2:
    st.title("₿ BTC Stacker Tracker")
    st.markdown("Track your Bitcoin holdings growth — full past years + projections (prices from CoinGecko)")

    col1, col2 = st.columns(2)

    with col1:
        initial_btc = st.number_input("Current BTC Held", min_value=0.0, value=1.0, step=0.000001, format="%.8f")
        annual_yield_pct = st.number_input("Annual Yield % (staking/lending)", min_value=0.0, value=0.0, step=0.5)

    with col2:
        assumed_growth_pct = st.number_input("Assumed Future Price Growth % p.a.", min_value=-90.0, value=30.0, step=5.0)
        project_years = st.number_input("Years to Project Forward", min_value=0, value=10, step=1)

    annual_yield = annual_yield_pct / 100
    annual_growth = assumed_growth_pct / 100

    @st.cache_data(ttl=900)  # 15 minutes cache
    def fetch_coingecko_prices():
        try:
            import requests
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,inr"
            response = requests.get(url, timeout=8)
            data = response.json()
            btc_usd = data['bitcoin']['usd']
            btc_inr = data['bitcoin']['inr']
            return btc_usd, btc_inr
        except Exception as e:
            st.warning(f"CoinGecko fetch failed: {str(e)}\nUsing fallback values.")
            return 85000.0, 7100000.0  # fallback ~$85k USD, ~₹71L INR

    btc_usd, btc_inr = fetch_coingecko_prices()

    current_value_inr = initial_btc * btc_inr
    st.metric(
        "Current Stack Value (INR)",
        f"₹{current_value_inr:,.0f}",
        f"{initial_btc:.8f} BTC @ ${btc_usd:,.0f} ≈ ₹{btc_inr:,.0f}"
    )

    # ── Build table — historical full years + projections ────────────
    table_rows = []
    btc_current = initial_btc
    prev_inr = None

    # Historical full past years (using yfinance for history)
    @st.cache_data(ttl=3600)
    def get_historical_btc():
        try:
            btc_hist = yf.download("BTC-USD", period="max", progress=False)['Close']
            return btc_hist
        except:
            return pd.Series()

    btc_hist = get_historical_btc()

    if not btc_hist.empty:
        yearly = btc_hist.resample('YE').last().dropna()
        past_years = [y for y in yearly.index.year if y < datetime.now().year]

        for yr in past_years:
            try:
                price_usd = yearly.loc[f"{yr}-12-31"]
                value_inr = btc_current * price_usd * btc_inr  # using current INR rate for approximation
                growth_pct = ((value_inr - prev_inr) / prev_inr * 100) if prev_inr is not None else None
                table_rows.append({
                    'Year': yr,
                    'BTC Held': f"{btc_current:.8f}",
                    'Value (₹)': f"₹{value_inr:,.0f}",
                    'Growth': f"{growth_pct:+.1f}%" if growth_pct is not None else "—"
                })
                prev_inr = value_inr
            except:
                pass

    # Projections (using current INR price)
    last_price_inr = btc_inr
    for i in range(1, project_years + 1):
        btc_current *= (1 + annual_yield)
        last_price_inr *= (1 + annual_growth)
        value_inr = btc_current * last_price_inr
        growth_pct = ((value_inr - prev_inr) / prev_inr * 100) if prev_inr is not None else None
        table_rows.append({
            'Year': datetime.now().year + i,
            'BTC Held': f"{btc_current:.8f}",
            'Value (₹)': f"₹{value_inr:,.0f}",
            'Growth': f"{growth_pct:+.1f}%" if growth_pct is not None else "—"
        })
        prev_inr = value_inr

    if table_rows:
        df_table = pd.DataFrame(table_rows)
        st.subheader("Yearly BTC Growth")
        st.dataframe(df_table, use_container_width=True, hide_index=True)

        # Chart
        years = df_table['Year']
        values = df_table['Value (₹)'].str.replace('₹', '').str.replace(',', '').astype(float)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(years, values, color='#f7931a', marker='o', linewidth=2.5)
        ax.set_xlabel("Year")
        ax.set_ylabel("Value (₹)")
        ax.grid(True, alpha=0.2)
        st.pyplot(fig)
    else:
        st.info("No data available yet — increase projection years or check internet connection.")

    with st.expander("Debug / Prices (from CoinGecko)"):
        st.write(f"Current BTC/USD: ${btc_usd:,.2f}")
        st.write(f"Current BTC/INR: ₹{btc_inr:,.0f}")
        st.write(f"Historical BTC data rows (yfinance): {len(btc_hist)}")


# ────────────────────────────────────────────────
# Expenses Tracker & Savings Analyzer
# ────────────────────────────────────────────────


with tab3:
    st.title("💰 Monthly Expenses & Savings Analyzer")
    st.markdown("Track every rupee — see detailed breakdown and how much you can actually save/invest.")

    # ── Monthly Income ───────────────────────────────────────────────
    monthly_income = st.number_input(
        "Monthly Income after Tax (₹)",
        min_value=0.0,
        value=123000.0,
        step=1000.0,
        format="%.0f",
        help="Your take-home pay after taxes"
    )

    # ── Fixed Expenses ───────────────────────────────────────────────
    st.subheader("Monthly Fixed Expenses (₹)")
    col_f1, col_f2 = st.columns(2)

    with col_f1:
        emi = st.number_input("EMI (e.g., Home Loan)", min_value=0.0, value=61742.0, step=1000.0, format="%.0f")
        society_maintenance = st.number_input("Society Maintenance", min_value=0.0, value=4448.0, step=500.0, format="%.0f")
        electricity_bill = st.number_input("Electricity Bill", min_value=0.0, value=1500.0, step=100.0, format="%.0f")
        gas_bill = st.number_input("Gas Bill", min_value=0.0, value=500.0, step=100.0, format="%.0f")

    with col_f2:
        money_to_mom = st.number_input("Money Transfer to Mom", min_value=0.0, value=3000.0, step=500.0, format="%.0f")
        money_to_wife = st.number_input("Money Transfer to Wife", min_value=0.0, value=2000.0, step=500.0, format="%.0f")
        other_fixed = st.number_input("Other Fixed (insurance, subscriptions)", min_value=0.0, value=0.0, step=500.0, format="%.0f")

    total_fixed = emi + society_maintenance + electricity_bill + gas_bill + money_to_mom + money_to_wife + other_fixed

    # ── Variable Expenses ────────────────────────────────────────────
    st.subheader("Monthly Variable Expenses (₹)")
    col_v1, col_v2 = st.columns(2)

    with col_v1:
        transportation = st.number_input("Transportation Cost", min_value=0.0, value=3000.0, step=500.0, format="%.0f")
        groceries = st.number_input("Groceries", min_value=0.0, value=8000.0, step=500.0, format="%.0f")
        dining = st.number_input("Dining Out", min_value=0.0, value=4000.0, step=500.0, format="%.0f")

    with col_v2:
        shopping = st.number_input("Shopping", min_value=0.0, value=5000.0, step=500.0, format="%.0f")
        bills_fees = st.number_input("Bills and Fees (other)", min_value=0.0, value=2000.0, step=500.0, format="%.0f")
        other_variable = st.number_input("Other Variable (e.g., entertainment)", min_value=0.0, value=0.0, step=500.0, format="%.0f")

    total_variable = transportation + groceries + dining + shopping + bills_fees + other_variable

    # ── Calculations ─────────────────────────────────────────────────
    total_expenses = total_fixed + total_variable
    savings = monthly_income - total_expenses
    savings_percent = (savings / monthly_income * 100) if monthly_income > 0 else 0
    expense_percent = (total_expenses / monthly_income * 100) if monthly_income > 0 else 0

    # ── Summary Metrics ──────────────────────────────────────────────
    st.subheader("Your Monthly Overview")
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Total Expenses", f"₹{total_expenses:,.0f}", f"{expense_percent:.1f}% of income")
    col_m2.metric("Savings / Breathing Space", f"₹{savings:,.0f}", f"{savings_percent:.1f}% of income")
    col_m3.metric("Fixed vs Variable", f"Fixed: ₹{total_fixed:,.0f}", f"Variable: ₹{total_variable:,.0f}")

    # ── Detailed Breakdown Data ──────────────────────────────────────
    expense_details = {
        'EMI': emi,
        'Society Maintenance': society_maintenance,
        'Electricity Bill': electricity_bill,
        'Gas Bill': gas_bill,
        'Transfer to Mom': money_to_mom,
        'Transfer to Wife': money_to_wife,
        'Other Fixed': other_fixed,
        'Transportation': transportation,
        'Groceries': groceries,
        'Dining Out': dining,
        'Shopping': shopping,
        'Bills & Fees': bills_fees,
        'Other Variable': other_variable,
        'Savings': max(savings, 0)
    }

    df_details = pd.DataFrame({
        'Category': list(expense_details.keys()),
        'Amount (₹)': list(expense_details.values())
    })

    if monthly_income > 0:
        df_details['% of Total Expenses'] = (df_details['Amount (₹)'] / total_expenses * 100).round(1).astype(str) + '%'
        df_details['% of Income'] = (df_details['Amount (₹)'] / monthly_income * 100).round(1).astype(str) + '%'
    else:
        df_details['% of Total Expenses'] = "—"
        df_details['% of Income'] = "—"

    # ── Clean Visuals (Full Income View) ─────────────────────────────
    if monthly_income > 0 and (total_fixed + total_variable + max(savings, 0)) > 0:
        st.subheader("Detailed Money Allocation (Income = 100%)")

        # Donut Chart — ALL categories including Savings
        fig_donut, ax_donut = plt.subplots(figsize=(9, 9))
        wedges, texts, autotexts = ax_donut.pie(
            df_details['Amount (₹)'],
            labels=df_details['Category'],
            autopct='%1.1f%%',
            pctdistance=1.15,           # push % labels further out
            labeldistance=1.3,          # push category labels further out
            startangle=90,
            wedgeprops=dict(width=0.5, edgecolor='white'),
            textprops={'fontsize': 9, 'fontweight':'bold'}
        )
        # Add center circle for donut effect
        centre_circle = plt.Circle((0,0), 0.65, fc='white')
        fig_donut.gca().add_artist(centre_circle)
        ax_donut.axis('equal')

        # Move legend outside to avoid clutter
        ax_donut.legend(wedges, df_details['Category'], title="Categories", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9)

        st.pyplot(fig_donut)

        # Horizontal Bar Chart — all categories
        st.subheader("Category-wise Comparison (All Items)")
        fig_bar, ax_bar = plt.subplots(figsize=(10, 9))
        bars = ax_bar.barh(df_details['Category'], df_details['Amount (₹)'], color=plt.cm.tab20.colors)
        ax_bar.set_xlabel("Amount (₹)")
        ax_bar.set_title("Full Monthly Breakdown (Income = 100%)")
        ax_bar.grid(True, axis='x', alpha=0.3)

        # Add value labels on bars
        for bar in bars:
            width = bar.get_width()
            ax_bar.text(width + max(df_details['Amount (₹)'])*0.02, bar.get_y() + bar.get_height()/2,
                        f"₹{width:,.0f}", va='center', fontsize=10)

        st.pyplot(fig_bar)

    else:
        st.info("Enter income and expenses to see detailed charts.")

    # ── Complete Table at Bottom ─────────────────────────────────────
    st.subheader("Complete Monthly Data Table (with Percentages)")
    st.dataframe(
        df_details.style.format({
            'Amount (₹)': '₹{:,.0f}'
        }),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")
    st.caption("Track regularly • Aim for 20–30% savings • Not financial advice")