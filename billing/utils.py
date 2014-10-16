# -*- coding: UTF-8 -*-
"""utils for billing module
@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license: AGPL v3 or newer (http://www.gnu.org/licenses/agpl-3.0.html)
"""

def compute_bill(bill):
    """Compute bill amount according to its details and save it"""
    if bill.state == "0_DRAFT":
        amount = 0
        amount_with_vat = 0
        for bill_detail in bill.billdetail_set.all():
            if bill_detail.amount:
                amount += bill_detail.amount
            if bill_detail.amount_with_vat:
                amount_with_vat += bill_detail.amount_with_vat
        if amount != 0:
            bill.amount = amount
        if amount_with_vat != 0:
            bill.amount_with_vat = amount_with_vat
    # Automatically compute amount with VAT if not defined
    if not bill.amount_with_vat:
        if bill.amount:
            bill.amount_with_vat = bill.amount * (1 + bill.vat / 100)
            # TODO: remove this, expense should be defined on detail level
            if bill.expenses.count():
                for expense in bill.expenses.all():
                    bill.amount_with_vat += expense.amount

    # Save it
    bill.save()