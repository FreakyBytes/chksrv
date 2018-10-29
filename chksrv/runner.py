# chksrv
# Copyright (C) 2018  Martin Peters

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
chksrv - runner and expect evaluator.
"""

import typing
import logging

from datetime import datetime, timedelta
import signal

from chksrv.checks import BaseCheck
from chksrv import exceptions


EVAL_GLOBALS = {
    'now': datetime.now,
    'timedelta': timedelta,
}


class CheckRunner(object):

    log = logging.getLogger('RUNNER')

    def __init__(self, check: BaseCheck, expects: typing.List[str], options: typing.Dict[str, typing.Any], retries: int=1, timeout: int=None):
        self._expects = None  # property
        self.check = check
        self.expects = expects
        self.options = options
        self.retries = max(1, int(retries))
        self.timeout = max(0, int(timeout)) if timeout else None

        self._compiled_expects = None
        self.expect_results = None
        self.expect_success = False
        self.success = False

    @property
    def results(self) -> typing.Dict[str, typing.Any]:
        return self.check.results

    @property
    def expects(self) -> typing.List[str]:
        return self._expects if hasattr(self, '_expects') else None

    @expects.setter
    def expects(self, expects):
        self._expects = expects

    def run(self):
        self.compile()

        self.expect_success = self.success = False

        for attempt in range(1, self.retries + 1):
            self.log.info(f"Attempt {attempt}/{self.retries}")
            self.run_check()
            self.evaluate_expects()

            check_success = all(filter(lambda item: item[0].endswith('.success'), self.results))
            self.success = check_success is True and self.check.results.get('success', False) is True and self.expect_success is True

            if self.success:
                break

            self.log.warn(' '.join([f"Attempt {attempt} failed.", "Retrying..." if attempt < self.retries else "Stop."]))

        return self.success

    def compile(self):
        """compiles the expect handlers."""

        if not self.expects:
            # no expects available
            self._compiled_expects = []
            return

        if self._compiled_expects:
            # expects already compiled or no expects available
            return

        self._compiled_expects = []
        for src in self.expects:
            try:
                self.log.debug(f"Compile expect: {src}")
                ast = compile(src, '<string>', 'eval', dont_inherit=True, optimize=2)
                self._compiled_expects.append(ast)

            except (SyntaxError, ValueError):
                self.log.exception(f"Cannot compile expect code: {src}")

    def run_check(self):
        if self.timeout:
            signal.signal(signal.SIGALRM, self._handle_timeout)
            signal.alarm(self.timeout)

        try:
            self.check.run()
        except exceptions.ChksrvTimeoutError:
            self.log.error(f"Check timed out after {self.timeout} seconds.", exc_info=False)
            self.check.results['results'] = False  # set check fail state
        finally:
            if self.timeout:
                signal.alarm(0)

    def evaluate_expects(self):

        if not self.results:
            self.log.error("There are no results from the check. Did it run?")
            raise exceptions.ChksrvNotReadyError("There are not results from the check.")

        if not self._compiled_expects:
            self.compile()

        eval_locals = {
            'res': self.results,
            'chk': self.check,
        }

        self.expect_results = []
        for expect in self._compiled_expects:
            try:
                res = eval(expect, EVAL_GLOBALS, eval_locals)
                self.expect_results.append(res)
                self.log.debug(f"Expect eval result: {res}")

                if not bool(res):
                    idx = self._compiled_expects.index(expect)
                    self.log.warn(f"Expect {idx} failed")

            except:
                self.expect_results.append(False)
                self.log.exception(f"Error while evaluating expect.")

        self.log.info("Expect evaluation done")
        self.expect_success = all(self.expect_results)
        self.log.info(f"Expects evaluated {'successful' if self.expect_success else 'failed'}")

        return self.expect_success

    def _handle_timeout(self, signum, frame):

        if signum == signal.SIGALRM:
            raise exceptions.ChksrvTimeoutError("Command timed out.")
