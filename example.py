from Loan import Loan
from optimize import LoanOptimizer
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import numpy as np
from typing import List
loans = [Loan(15000, 8.3),
        Loan(75000, 4.0),
        Loan(20000, 5.7)]

loan_opt = LoanOptimizer(loans, payment_period=relativedelta(months=1))
def single_run_optimize(initial_payment: float, period_payment: float, pay_interest=True):
    """Optimize over single set of parameters and generate graphs
        
        Keyword Arguments:
        initial_payment -- amount of money that can be used to payment loans at the begining of the simulation
        period_payment  -- amount of money that can be used to pay loans each payment period (as defined in constructor)
        pay_interest    -- force interest to be paid off every payment period (sometimes optimum strategies let low interest loans grow while concentrating on high interest ones, however, your credit score will appreciate you making all your payments)"""
    (total_paid, payment_time, initial_payment_amounts, period_payment_amounts, loan_balances, loan_payments) = loan_opt.optimize(initial_payment=initial_payment, period_payment=period_payment, pay_interest=pay_interest, debug_print=False)
    loan_balances.plot()
    plt.title('Loan Balances Over Time')
    plt.xlabel('Date')
    plt.ylabel('Balance ($)')
    plt.savefig('loan_balances.png', dpi=300)
    loan_payments.iloc[1:].plot()
    plt.title('Loan Payments Over Time')
    plt.xlabel('Date')
    plt.ylabel('Payment ($)')
    plt.savefig('loan_payments.png', dpi=300)
    print(f"Paid ${total_paid} in {payment_time.days} days")
    print("Initial Payment Amounts:")
    print(initial_payment_amounts)
    print("First Month Payment Amounts:")
    print(period_payment_amounts)

def many_run_analysis(initial_payments: List[float], period_payments: List[float], pay_interest=True):
    """Sweep parameters and generate contour plot of total payment
    
        Keyword Arguments:
        initial_payments -- Range: amount of money that can be used to payment loans at the begining of the simulation
        period_payments  -- Range: amount of money that can be used to pay loans each payment period (as defined in constructor)
        pay_interest     -- force interest to be paid off every payment period (sometimes optimum strategies let low interest loans grow while concentrating on high interest ones, however, your credit score will appreciate you making all your payments)"""
    total_payments = []
    for idx, initial_payment in enumerate(initial_payments):
        total_payments.append([])
        for period_payment in period_payments:
            print(f'Trying intial: {initial_payment}, monthly: {period_payment}')
            (total_paid, _, _, _, _, _) = loan_opt.optimize(initial_payment, period_payment, pay_interest=pay_interest)
            total_payments[idx].append(total_paid)

    levels = range(int(np.min(total_payments)/500)*500, int(np.max(total_payments)/500 + 1)*500, 500)
    plt.clf()
    plt.cla()
    cont = plt.contour(period_payments, initial_payments, total_payments, levels)
    plt.xlabel("Montly Payment ($)")
    plt.ylabel("Initial payment ($)")
    plt.title("Total Payment as a Function of\n Initial and Period Payment Amounts")
    plt.clabel(cont, inline=True, fontsize=10)
    plt.savefig("total_payment_graph.png", dpi=300)

single_run_optimize(10000,1200)
#many_run_analysis(range(8000,13000,1000), range(900,1500, 50))