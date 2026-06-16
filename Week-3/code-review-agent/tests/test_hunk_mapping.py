"""Unit tests for diff hunk parsing and the line-in-hunk guard."""
from app.tools.github import finding_in_hunk, line_in_hunk, parse_diff

# A modify-in-place diff: hunk covers new-file lines 10..13 (3 ctx + 1 added).
_MODIFY_DIFF = """\
diff --git a/foo.py b/foo.py
--- a/foo.py
+++ b/foo.py
@@ -10,3 +10,4 @@ def f():
 ctx1
+added
 ctx2
 ctx3
"""

# A new-file diff: hunk covers new-file lines 1..3.
_NEWFILE_DIFF = """\
diff --git a/bar.py b/bar.py
new file mode 100644
--- /dev/null
+++ b/bar.py
@@ -0,0 +1,3 @@
+line1
+line2
+line3
"""


def test_parse_diff_modify_hunk_ranges():
    hunks = parse_diff(_MODIFY_DIFF)
    assert set(hunks) == {"foo.py"}
    h = hunks["foo.py"][0]
    assert (h["new_start"], h["new_count"]) == (10, 4)
    assert (h["old_start"], h["old_count"]) == (10, 3)
    assert h["added_lines"] == [11]  # the single '+added' line


def test_line_inside_hunk_is_true():
    hunks = parse_diff(_MODIFY_DIFF)
    for line in (10, 11, 12, 13):
        assert line_in_hunk("foo.py", line, "RIGHT", hunks) is True


def test_adjacent_line_is_false():
    hunks = parse_diff(_MODIFY_DIFF)
    assert line_in_hunk("foo.py", 9, "RIGHT", hunks) is False   # just before
    assert line_in_hunk("foo.py", 14, "RIGHT", hunks) is False  # just after


def test_unknown_path_is_false():
    hunks = parse_diff(_MODIFY_DIFF)
    assert line_in_hunk("other.py", 11, "RIGHT", hunks) is False


def test_newfile_hunk_membership():
    hunks = parse_diff(_NEWFILE_DIFF)
    assert line_in_hunk("bar.py", 1, "RIGHT", hunks) is True
    assert line_in_hunk("bar.py", 3, "RIGHT", hunks) is True
    assert line_in_hunk("bar.py", 4, "RIGHT", hunks) is False


def test_finding_in_hunk_wrapper():
    hunks = parse_diff(_MODIFY_DIFF)
    in_finding = {"path": "foo.py", "line": 11, "side": "RIGHT"}
    out_finding = {"path": "foo.py", "line": 99, "side": "RIGHT"}
    assert finding_in_hunk(in_finding, hunks) is True
    assert finding_in_hunk(out_finding, hunks) is False
