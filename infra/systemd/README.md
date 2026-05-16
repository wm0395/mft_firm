# systemd Templates

These files are templates for the native WSL/Linux deployment path.

## Files

- `market-data-import.service`
- `market-data-import.timer`
- `mft-research-worker.service`

## Intent

- Keep the first operational surface small.
- Use systemd only for controlled scheduled or long-running tasks.
- Keep application logic out of unit files.

## Usage

Copy or adapt the templates into `/etc/systemd/system/`, then update:

- `WorkingDirectory`
- `EnvironmentFile`
- `ExecStart`
- `User`

The current files are placeholders only.
They document the intended service shape before the application wiring exists.
