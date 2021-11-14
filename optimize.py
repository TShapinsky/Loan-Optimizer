from typing import Dict, List
from Loan import Loan
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
import copy
from skopt import gp_minimize, forest_minimize, gbrt_minimize
import pandas as pd
from typing import Tuple

class LoanOptimizer:
    def __init__(self, loans: List[Loan], start_date: datetime=datetime(2022,2,1), payment_period: relativedelta=relativedelta(months=1)):
        """Construct Loan Optimizer
        
        Keyword Arguments:
        loans          -- list of loan objects to optimize over
        start_date     -- when loan payment starts
        payment_period -- how often should a payment be made on the loans (default: 1 month)"""
        self.start_date = start_date
        self.payment_period = payment_period
        self.loans = loans

    def simulate(self, initial_payment: float, period_payment: float, *splits, pay_interest=False, debug_print=False) -> Tuple[float, relativedelta, DataFrame, DataFrame]:
        loans = [copy.copy(loan) for loan in self.loans]
        date = copy.copy(self.start_date)
        total_paid = 0
        splits = splits[0]
        initial_splits = splits[0:len(self.loans)-1]
        period_splits = splits[len(self.loans)-1:]

        initial_payment_amounts = self.splits_to_amounts(initial_payment, initial_splits)
        date_index = pd.DatetimeIndex([date])
        loan_names = [f'Loan {idx}' for idx in range(len(loans))]
        loan_balances = pd.DataFrame(index = date_index, columns=loan_names)
        loan_payments = pd.DataFrame(index = date_index, columns=loan_names)

        loan_payments.loc[date] = initial_payment_amounts
        for idx, loan in enumerate(loans):
            loan.start(self.start_date)
            total_paid = total_paid + loan.pay(initial_payment_amounts[idx])
            loan_balances.loc[date, loan_names[idx]] = loan.get_balance()



        while date < self.start_date + relativedelta(years=10):
            date = date+ self.payment_period
            period_paid = 0
            remaining_payment=period_payment
            for idx, loan in enumerate(loans):
                loan.simulate(date, debug_print)
                loan_payments.loc[date, loan_names[idx]] = 0
                if pay_interest:
                    if remaining_payment > loan.interest:
                        debug_print and print(f'Paying interest: {loan.interest}, {date}')
                        period_paid += loan.interest
                        loan_payments.loc[date, loan_names[idx]] += loan.interest
                        remaining_payment -= loan.pay(loan.interest)
            period_payment_amounts = self.splits_to_amounts(remaining_payment, period_splits)
            
            period_payments = self.pay_loans(loans, period_payment_amounts)
            loan_payments.loc[date] += [period_payments[loan] for loan in loans]
            period_paid += sum(period_payments.values())
            assert int(period_paid) <= int(period_payment)
            total_paid += period_paid
            remaining_balance = 0
            for idx, loan in enumerate(loans):
                remaining_balance += loan.get_balance()
                loan_balances.loc[date, loan_names[idx]] = loan.get_balance()
            if period_paid == 0 and remaining_balance == 0:
                return (total_paid, date - self.start_date, loan_balances, loan_payments)

        remaining = 0

        for loan in loans:
            remaining = remaining + loan.principal + loan.interest
        return (remaining + total_paid, relativedelta(years=10), loan_balances, loan_payments)

    def pay_loans(self, loans: List[Loan], payments: List[float], debug_print=False) -> Dict[Loan, float]:
        amount_paid = {}
        unpaid_loans = []
        unpaid_loan_payments = []
        left_over_payments = 0
        for idx, loan in enumerate(loans):
            loan_amount_paid = loan.pay(payments[idx], debug_print=debug_print)
            if loan.principal + loan.interest > 0:
                unpaid_loans.append(loan)
                unpaid_loan_payments.append(payments[idx])
            else:
                left_over_payments += payments[idx] - loan_amount_paid
            amount_paid[loan] = loan_amount_paid
        
        if left_over_payments == 0:
            return amount_paid
        else:
            new_payments = []
            for idx, loan in enumerate(unpaid_loans):
                if sum(unpaid_loan_payments) == 0:
                    return amount_paid
                new_payments.append(unpaid_loan_payments[idx]/sum(unpaid_loan_payments)*left_over_payments)
            for loan, amount in self.pay_loans(unpaid_loans, new_payments).items():
                amount_paid[loan] += amount
            return amount_paid

    def splits_to_amounts(self, amount: float, splits: List[float]) -> float:
        amounts = []
        for split in splits:
            specific_amount = amount*split
            amounts.append(specific_amount)
            amount = amount - specific_amount
        amounts.append(amount)
        return amounts

    def optimize(self, initial_payment: float, period_payment: float, pay_interest=False, debug_print=False) -> Tuple[float, relativedelta, List[float], List[float], DataFrame, DataFrame]:
        """Optimize loan repayment strategy for given constraints
        
        Keyword Arguments:
        initial_payment -- amount of money that can be used to payment loans at the begining of the simulation
        period_payment  -- amount of money that can be used to pay loans each payment period (as defined in constructor)
        pay_interest    -- force interest to be paid off every payment period (sometimes optimum strategies let low interest loans grow while concentrating on high interest ones, however, your credit score will appreciate you making all your payments)
        
        Returns:
        Parameters of optimized loan repayment strategy
        (total_paid, payment_time, initial_payment_amounts, period_payment_amount, loan_balances)
        total_paid              -- total amount used to pay loans
        payment_time            -- amount of time uesed to pay loans
        initial_payment_amounts -- splits of how much to initially payment each loan
        period_payment_amounts  -- splits of how much to pay each loan each payment period
        loan_balances            -- loan balances over time during repayment
        loan_payments           -- loan payments over time during repayment
        """
        def optimize_simulate(*args):
            (total_paid, _, _, _) = self.simulate(initial_payment, period_payment, *args, pay_interest=pay_interest)
            return total_paid

        res = gbrt_minimize(optimize_simulate, [(0.0, 1.0)]*(len(self.loans)*2 - 2), n_calls=100, x0=[0.5]*(len(self.loans)*2 - 2), n_initial_points = 20)
        (total_paid, payment_time, loan_balances, loan_payments) = self.simulate(initial_payment, period_payment, res.x, pay_interest=pay_interest, debug_print=debug_print)
        initial_payment_amounts = loan_payments.iloc[0]
        period_payment_amounts = loan_payments.iloc[1]
        return (total_paid, payment_time, initial_payment_amounts, period_payment_amounts, loan_balances, loan_payments)
    