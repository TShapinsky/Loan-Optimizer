from Loan import Loan
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
import copy
from skopt import gp_minimize
import matplotlib.pyplot as plt

class LoanOptimizer:
    def __init__(self, loans, payment_period=relativedelta(months=1)):
        self.start_date = datetime(2022,1,1)
        self.payment_period = payment_period
        self.loans = loans

    def simulate(self, initial_paydown, period_payment, *args, graph=False):
        loans = [copy.copy(loan) for loan in self.loans]
        date = copy.copy(self.start_date)
        total_paid = 0
        #print(args)
        args = args[0]
        initial_splits = args[0:len(self.loans)-1]
        #print(initial_splits)
        period_splits = args[len(self.loans)-1:]
        period_splits = np.reshape(period_splits, (len(initial_splits), int(len(period_splits)/len(initial_splits))))

        initial_paydown_amounts = self.splits_to_amounts(initial_paydown, initial_splits)
        loan_history = []

        for idx, loan in enumerate(loans):
            loan.start(self.start_date)
            loan_history.append([loan.get_balance()])
            total_paid = total_paid + loan.pay(initial_paydown_amounts[idx])

        i = 0
        while date < self.start_date + relativedelta(years=10):
            period_payment_amounts = self.function_splits_to_amounts(period_payment, period_splits, i)
            #print(period_payment_amounts)
            date = date+ self.payment_period
            period_paid = 0
            for idx, loan in enumerate(loans):
                loan.simulate(date)
            period_paid = self.pay_loans(loans, period_payment_amounts)
            assert int(period_paid) <= int(period_payment)
            total_paid += period_paid
            remaining_balance = 0
            for idx, loan in enumerate(loans):
                remaining_balance += loan.get_balance()
                loan_history[idx].append(loan.get_balance())
            if period_paid == 0 and remaining_balance == 0:
                if graph:
                    for loan_values in loan_history:
                        plt.plot(loan_values)
                        print(loan_values)
                    plt.savefig("balances_over_time.png")
                return (total_paid, date - self.start_date)
            i+= 1

        remaining = 0

        for loan in loans:
            remaining = remaining + loan.principal + loan.interest
        return (remaining + total_paid, 120)

    def pay_loans(self, loans, payments):
        amount_paid = 0
        unpaid_loans = []
        unpaid_loan_payments = []
        left_over_payments = 0
        for idx, loan in enumerate(loans):
            loan_amount_paid = loan.pay(payments[idx])
            if loan.principal + loan.interest > 0:
                unpaid_loans.append(loan)
                unpaid_loan_payments.append(payments[idx])
            else:
                left_over_payments += payments[idx] - loan_amount_paid
            amount_paid += loan_amount_paid
        
        if left_over_payments == 0:
            return amount_paid
        else:
            new_payments = []
            for idx, loan in enumerate(unpaid_loans):
                if sum(unpaid_loan_payments) == 0:
                    return amount_paid
                new_payments.append(unpaid_loan_payments[idx]/sum(unpaid_loan_payments)*left_over_payments)
            return amount_paid + self.pay_loans(unpaid_loans, new_payments)

    def splits_to_amounts(self, amount, splits):
        amounts = []
        for split in splits:
            specific_amount = amount*split
            amounts.append(specific_amount)
            amount = amount - specific_amount
        amounts.append(amount)
        return amounts

    def function_splits_to_amounts(self, amount, function_splits, x):
        amounts = []
        for function_split in function_splits:
            split = function_split[0] + function_split[1]*(x-function_split[2])
            #for idx, c in enumerate(function_split):
            #    split += c*(x**idx)
            #print(split)
            split = min(max(split,0), 1)
            specific_amount = amount*split
            amounts.append(specific_amount)
            amount = amount - specific_amount
        amounts.append(amount)
        return amounts

    def optimize(self, initial_paydown, period_payment):
        def optimize_simulate(*args):
            (total_paid, payment_time) = self.simulate(initial_paydown, period_payment, *args)
            return total_paid

        params = [(0.0,1.0)]*(len(self.loans)*2 - 2)
        split_count = len(self.loans) -1
        res = gp_minimize(optimize_simulate, [(0.0, 1.0)]*split_count + [(0.0,1.0),(-1.0,1.0),(-100.0,100.0)]*split_count, n_calls=200, x0=[0.5]*split_count + [0.5,0,0]*split_count, n_initial_points = 20, acq_optimizer="lbfgs", n_jobs=-1)
        initial_splits = res.x[0:len(self.loans)-1]
        period_splits = res.x[len(self.loans)-1:]
        period_splits = np.reshape(period_splits, (len(initial_splits), int(len(period_splits)/len(initial_splits))))
        initial_paydown_amounts = self.splits_to_amounts(initial_paydown, initial_splits)
        period_payment_amounts = self.function_splits_to_amounts(period_payment, period_splits, 0)
        (total_paid, payment_time) = self.simulate(initial_paydown, period_payment, res.x, graph=True)
        return (total_paid, payment_time, initial_paydown_amounts, period_payment_amounts)
    