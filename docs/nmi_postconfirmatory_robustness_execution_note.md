# NMI robustness execution note

The post-confirmatory robustness suite is executed through RunRelay from a dedicated exact-commit execution branch so the long-standing main-branch RunRelay task manifest does not need to be rewritten solely to add one temporary reviewer-driven task. The execution branch remains a descendant of main and contains the same scientific code plus a minimal safe RunRelay manifest that permits only the frozen robustness suite. The scientific scripts and protocol themselves are committed on main.
