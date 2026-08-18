# utils/branches.py
#
# Edit this list to match your bank's real branch names.

BRANCHES = [
    "Koramangala",
    "Indiranagar",
    "Whitefield",
    "MG Road",
    "Jayanagar",
    "Electronic City",
]


def select_branch(prompt="Select Branch:"):
    """
    Shows a numbered list of branches and keeps asking until the user
    picks a valid one. Returns the branch name (not the number).
    """
    print(f"\n{prompt}")

    for i, branch in enumerate(BRANCHES, start=1):
        print(f"{i}. {branch}")

    while True:
        raw = input("Enter choice number: ").strip()

        if raw.isdigit() and 1 <= int(raw) <= len(BRANCHES):
            return BRANCHES[int(raw) - 1]

        print(f"Please enter a number between 1 and {len(BRANCHES)}.")