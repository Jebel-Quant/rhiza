# Troubleshooting

Common Rhiza sync failures and quick recovery steps.

## 1) Bundle not found

- **Error pattern**
  ```text
  Bundle directory does not exist: bundles/<bundle-name>
  ```
- **Root cause**  
  A bundle name in your template/profile config does not exist in the selected Rhiza ref.
- **Recovery**
  ```bash
  make explain-bundles
  # fix bundle names in .rhiza/template.yml (or your profile selection), then:
  make sync
  ```

## 2) File conflict between bundles

- **Error pattern**
  ```text
  File ownership conflicts in (<bundle>×<platform>) combination:
  ```
- **Root cause**  
  Two selected bundles claim the same destination path.
- **Recovery**
  ```bash
  make explain-bundles
  # remove one conflicting bundle (or use an explicit profile), then:
  make sync
  ```

## 3) Sync leaves partial state

- **Error pattern**
  ```text
  [ERROR] Failed to install dependencies
  ```
  (or another command failure during `make sync`/`make install`)
- **Root cause**  
  Sync applies file changes before later setup/install steps run. A later failure does not roll files back automatically.
- **Recovery**
  ```bash
  git status
  git restore .
  git clean -fd
  make sync
  ```
