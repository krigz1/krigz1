# DIAGNOSIS QUICK GUIDE

## Récupérer un Run ID GitHub Actions
1. Ouvrir **Actions**.
2. Ouvrir le workflow en échec.
3. Le Run ID est visible dans l'URL et dans les métadonnées du run.

## Où trouver UBT Log.txt
- Windows (typique): `C:\Users\<USER>\AppData\Local\UnrealBuildTool\Log.txt`
- Linux (selon setup): `~/.config/Epic/UnrealBuildTool/Log.txt`

## Commandes build locales
### Linux
```bash
bash Scripts/build_and_run.sh --target editor
Windows PowerShell
.\Scripts\build_and_run.ps1 -Target editor
Git LFS
git lfs install --local
git lfs pull
git lfs ls-files
Validation diagnostics locale
Linux/macOS
bash Scripts/ci/validate_repo.sh
Windows PowerShell
.\Scripts\ci\validate_repo.ps1
Règles logs

Ne jamais inclure secrets/tokens.

Limiter les extraits à ~30–40 lignes.


<<<<<<< HEAD
=======
- Windows (typique): `C:\Users\<user>\AppData\Local\UnrealBuildTool\Log.txt`
- Linux (selon setup): `~/.config/Epic/UnrealBuildTool/Log.txt`

## Commandes build locales
- Linux:
  ```bash
  bash Scripts/build_and_run.sh --target editor
  ```
- Windows PowerShell:
  ```powershell
  .\Scripts\build_and_run.ps1 -Target editor
  ```

## Git LFS
```bash
git lfs install
git lfs pull
git lfs ls-files
```

## Validation diagnostics locale
- Linux/macOS:
  ```bash
  bash Scripts/ci/validate_repo.sh
  ```
- Windows PowerShell:
  ```powershell
  .\Scripts\ci\validate_repo.ps1
  ```

## Règles logs
- Ne jamais inclure secrets/tokens.
- Limiter les extraits à ~30–40 lignes.
>>>>>>> origin/main
