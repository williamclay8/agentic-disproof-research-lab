# Trading Kernel Boundary

The canonical kernel code currently lives in `src/trading_lab`.

This package directory exists to make the product boundary explicit before a
larger packaging move:

- Kernel code stays deterministic, artifact-first, and testable offline.
- Kernel code must not import HTTP servers, databases, queues, auth, secrets,
  brokers, order routing, or scheduler infrastructure.
- Product apps wrap the kernel through typed artifacts and narrow service
  functions.
- Generated reports and runs are evidence artifacts, not the production app
  database.

When the repo is ready for a larger move, this directory can become the actual
Python package home or a packaging facade. Until then, avoid churn in import
paths and keep tests pointed at `src/trading_lab`.
