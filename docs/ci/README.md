# CI activation

The workflow is stored here inertly so it can be reviewed and pushed without requiring GitHub workflow mutation during the build.

Activate it from the repository root:

```bash
mkdir -p .github/workflows
cp docs/ci/site-pipeline.yml .github/workflows/site-pipeline.yml
git add .github/workflows/site-pipeline.yml
git commit -m "Activate interactive pipeline CI"
git push origin main
```

The workflow installs pinned dependencies, regenerates both static extracts, fails on any generated diff, runs the data/public-claim suite, and checks the browser JavaScript syntax.
