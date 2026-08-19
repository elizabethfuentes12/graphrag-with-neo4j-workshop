# Questions for the repo author

Two things need your decision. We did not guess, because both are hard to undo.

---

## 1. Which images folder is the real one?

There are two image folders. They hold the same 11 files. The files are exactly the same,
byte for byte. Both are checked into git.

- `static/images/`
- `workshop-content/images/`

We want to keep one and delete the other. We do not know which one you meant to keep.

Here is what points each way:

- The markdown pages link to `workshop-content/images/`. So that one is in use today.
- AWS Workshop Studio normally expects a `static/` folder at the top of the repo. So that
  one may be the one the platform wants.

**Question: which folder should we keep?**

- [ ] Keep `workshop-content/images/`
- [ ] Keep `static/images/`
- [ ] Something else (please say what)

---

## 2. Should the workshop code be installed as a package?

Right now every notebook starts with a cell that adds a folder to the Python path. It looks
like this:

```python
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "..")))
```

That cell is what lets a notebook run `from workshop.contracts import MAX_GUESTS`.

There is another way to do it. We could add a `pyproject.toml` file and install the code
once at setup. Then those path cells are not needed and we can delete them from all six
notebooks.

Both ways work. This is a preference, not a bug.

- Keeping the path cells: nothing changes, it works today.
- Installing as a package: the notebooks get cleaner, and the setup step does the work
  instead.

**Question: which do you want?**

- [ ] Keep the path cells as they are
- [ ] Add `pyproject.toml` and delete the path cells

### One thing to know first

We found a problem in the setup while looking at this. The `README.md` says to run:

```
uv venv && uv pip install -r requirements.txt
```

That command puts the packages in a folder called `.venv`. But the notebooks run on the
system Python at `/usr/bin/python3.13`, not on `.venv`. So the notebooks cannot see any of
those packages, and the labs fail on the first import.

This is a separate bug from the question above. It needs fixing either way. We just want to
flag that it is there, because it also decides how a package install would need to be done.
