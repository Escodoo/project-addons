To configure this module, you need to:

#. Enable **Analytic Accounting** (Settings → Accounting).
#. Assign users who may set the percentage and approve over-budget
   purchase orders to the group **Project Purchase Budget Manager**
   (project managers get this group automatically via implication).
#. Open *Settings → Technical → Tier Validations → Tier Definition* and
   confirm the record **Purchase exceeds project budget** exists:

   * Model: Purchase Order
   * Definition type: Formula
   * Expression: ``rec.exceeds_project_purchase_budget``
   * Reviewer group: Project Purchase Budget Manager

#. Optionally add a second tier definition (higher sequence) for a
   superior approval group if two approval levels are required.


