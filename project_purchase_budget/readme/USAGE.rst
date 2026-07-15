To use this module, you need to:

* Create or open a project with an analytic account.
* Link a confirmed sales order (billable project + sales order item)
  **or** set **Sale Amount Override** on the project.
* Set **Purchase Budget %** (e.g. ``60`` for 60%).
* Create purchase orders with analytic distribution on the project
  analytic account.
* If the purchase order would exceed the budget, a warning appears and
  tier validation must be requested/approved before confirmation.
* On the project **Purchase Budget** tab, review:

  * Purchase Budget (planned)
  * Purchase Spent (actual / committed)
  * Purchase Remaining and Consumed %
  * Project Contribution (sale − spent)
