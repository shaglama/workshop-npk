# How changes reach `main`

1. **`main` holds reviewed work only.** Changes arrive by pull request, and a pull request is merged only after review.
2. **Work happens on branches** named `work/<project>` (for example `work/commonmark`), or `work/<project>-<topic>` for a separate piece.
3. **Each project's manager** opens the pull request when a piece is ready. Its description says:
   - what changed
   - how it was tested, with the commands and their results
   - who wrote and who reviewed each part
4. **The reviewer** re-runs the tests before merging. Anything that needs changes goes back as review comments on the pull request.
5. **A possible compiler fault** found while working goes in the pull request description under "Compiler notes": the smallest program that shows it, the compiler commit, and what happened against what was expected. It's checked and passed to the compiler project from there. The project works around it meanwhile.
