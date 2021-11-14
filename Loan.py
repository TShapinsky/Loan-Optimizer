import numpy as np
from dateutil.relativedelta import relativedelta
from datetime import datetime
class Loan:
    """Class Loan provides an interface to simulate how a loan reacts to payment and the passage of time"""
    def __init__(self, principal: float, apr: float, interest_period: relativedelta = relativedelta(days=1), capitalization_period: relativedelta = relativedelta(months = 4)):
        """Construct a loan
        
        Keyword Arguments:
        principal             -- The principal balance of the loan
        apr                   -- The annualized interest rate of the loan
        interest_period       -- How often interest is added to the loan's interest (default: 1 day)
        capitalization_period -- After how long of being unpaid is interest added to the principal (default: 4 months)"""
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

    def start(self, date: datetime) -> None:
        """Initializes the loan simulation
        Should be called before simulate
        
        Keyword Argument:
        date -- The initialization date of the loan simulation (interest will start accruing from this date)"""
        self.date = date
        self.last_paid = date

    def simulate(self, date: datetime, debug_print=False) -> None:
        """Simulate loan behavior to date
        
        Keyword Argument:
        date -- when to simulate loan till"""
        while self.date < date:
            self.date = self.date + self.interest_period
            self.interest = self.interest + self.principal * (self.interest_rate)
            if self.last_paid + self.capitalization_period < self.date and self.principal > 0:
                debug_print and print(f"capitalizing interest: {self.interest}, {self.date}")
                self.principal = self.principal + self.interest
                self.interest = 0

    def get_balance(self) -> float:
        """Gets Loan Balance"""
        return self.principal + self.interest

    def pay(self, pay_amount: float, debug_print=False) -> float:
        """Pay loan
        Interest is paid first
        
        Keyword Argument:
        pay_amount -- how much to pay down the loan
        
        Return:
        total_paid -- may be less than pay_amount if the balance is less than the pay_amount"""
        total_paid = 0
        if pay_amount >= self.interest:
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