# Notebooks

Notebook use here is inspection only.

Use the CLI to create projects, run parameter research, compare runs, and
export packs. Read notebooks should load exported artifacts or snapshot
metadata, then produce notes or charts without writing back to the database.

Do not:

- call `DataRepository` write methods
- create or update schema objects
- modify research tables from notebook cells
- treat notebook variables as the source of truth
