import numpy as np
from dateutil.relativedelta import relativedelta
from datetime import datetime
class Loan:
    def __init__(self, principal, apr, interest_period: relativedelta = relativedelta(days=1), capitalization_period: relativedelta = relativedelta(months = 1)):
        self.principal = principal
        self.interest = 0
        interest_periods_per_year = 365
        if interest_period.months > 0:
            interest_periods_per_year = 12/interest_period.months
        elif interest_period.days > 0:
            interest_periods_per_year = 365/interest_period.days
        self.interest_rate = apr/interest_periods_per_year/100.0
        self.interest_period = interest_period
        self.capitalization_period = capitalization_period

    def start(self, date: datetime):
        self.date = date
        self.last_paid = date

    def simulate(self, date):
        while self.date < date:
            self.date = self.date + self.interest_period
            self.interest = self.interest + self.principal * (self.interest_rate)
            if self.last_paid + self.capitalization_period < self.date and self.principal > 0:
                #print(f"capitalizing interest: {self.date}")
                self.principal = self.principal + self.interest
                self.interest = 0

    def get_balance(self):
        return self.principal + self.interest

    def pay(self, pay_amount):
        total_paid = 0
        if pay_amount > self.interest:
            total_paid = self.interest
            pay_amount = pay_amount - self.interest
            self.interest = 0
            self.last_paid = self.date
        else:
            self.interest = self.interest - pay_amount
            total_paid = pay_amount
            pay_amount = 0
        if pay_amount > self.principal:
            total_paid = total_paid + self.principal
            self.principal  = 0
        else:
            self.principal = self.principal - pay_amount
            total_paid = total_paid + pay_amount

        return total_paid