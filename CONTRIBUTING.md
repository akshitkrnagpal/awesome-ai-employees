# Contributing

Thanks for helping improve Awesome AI Employees.

This repo tracks companies that publicly position their products as AI employees, digital workers, AI teammates, role-based agents, or AI leaders for a recurring business function.

## What Belongs

Good additions usually meet at least one of these criteria:

- The product is described as an AI employee, digital worker, AI teammate, named agent, or role-based worker.
- The product owns a recurring business workflow, such as sales development, support, recruiting, finance, legal, engineering, security, or healthcare operations.
- The company has a public page where the positioning can be verified.

## What Does Not Belong

Please avoid submitting:

- Generic LLM APIs or model providers.
- Basic chatbot builders without a clear job or business-function angle.
- Thin AI features inside a broader product.
- Stealth companies or private demos without a public product page.
- Companies where the evidence URL does not support the AI employee angle.

## Submission Checklist

For each suggested company, include:

- Company name.
- Public product or landing page URL.
- Suggested category.
- One-sentence AI employee angle.
- Optional notes on role name, customer type, autonomy, human-in-the-loop behavior, integrations, or pricing.

## Pull Request Style

- Treat `data/companies.csv` as the source of truth for the list.
- Run `make generate` after editing `data/companies.csv`.
- Run `make check` before opening a pull request.
- Keep entries alphabetically stable only within their existing numbered section if possible.
- Keep descriptions short and factual.
- Prefer the most specific product page over the company homepage.
- Do not add affiliate links, tracking parameters, or promotional copy.
- If you are affiliated with a submitted company, say so in the pull request.

## Maintenance Notes

Listings may be removed if the product page disappears, the AI worker positioning is no longer visible, or the company shifts away from the category.
