# flake8: noqa: E202,E241

import unittest
from math import inf

from packaging.specifiers import Specifier

import lib.requirements as r

# fmt: off
conversions = [
    ("==1",       ((1,),         (1,)            ), "==1"           ),
    ("==1.0",     ((1, 0),       (1, 0)          ), "==1.0"         ),
    ("==1.2.3",   ((1, 2, 3),    (1, 2, 3)       ), "==1.2.3"       ),
    ("~=1.2.3",   ((1, 2, 3),    (1, 2, inf)     ), "~=1.2.3"       ),
    ("~=1.2.3.4", ((1, 2, 3, 4), (1, 2, inf, inf)), "~=1.2.3.4"     ),
    (">=2.0",     ((2, 0),       (inf, inf)      ), ">=2.0"         ),
    (">3.1",      ((3, 2),       (inf, inf)      ), ">=3.2"         ),
    ("<4.2",      ((-inf, -inf), (4, 2)          ), "<4.2"          ),
    ("<=5.3",     ((-inf, -inf), (5, 4)          ), "<5.4"          ),
]
# fmt: on


class Test(unittest.TestCase):
    def setUp(self):
        self.addTypeEqualityFunc(r.Requirement, self.assertRequirementEqual)

    def assertRequirementEqual(self, a: r.Requirement, b: r.Requirement, msg=None):
        return self.assertEqual(str(a), str(b), msg=msg)

    def test_specifier_to_interval(self):
        for s, expected, _ in conversions:
            self.assertEqual(r.specifier_to_interval(Specifier(s)), expected)

    def test_interval_to_specifier_str(self):
        for _, x, expected in conversions:
            self.assertEqual(r.interval_to_specifier_str(x), expected)

    def test_merge_requirements(self):
        should_succeed = [
            (("a == 1.0", "a==1.0"), "a==1.0"),
            (("a == 1.2.3", "a==1.2"), "a==1.2.3"),
            (("a ~= 1.2.3", "a==1.2"), "a~=1.2.3"),
        ]
        should_fail = [
            (("a == 1.0", "a==2.0"), "cannot merge version specifiers"),
            (("a ~= 1.0", "a==2.0"), "cannot merge version specifiers"),
            (("a < 1.0", "a > 1.0"), "cannot merge version specifiers"),
        ]
        for (a, b), c in should_succeed:
            ra, rb, rc = r.Requirement(a), r.Requirement(b), r.Requirement(c)
            self.assertEqual(r.merge_requirements(ra, rb), rc)
        for (a, b), msg in should_fail:
            ra, rb = r.Requirement(a), r.Requirement(b)
            with self.assertRaisesRegex(Exception, msg):
                r.merge_requirements(ra, rb)
