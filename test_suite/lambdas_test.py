import os

from base import TestBase

class LambdasTest(TestBase):
    snippet_dir = "lambdas"

    def test_lambda_call(self):
        self.validate_snippet(self.get_snippet_path("call"))

    def test_lambda_calls_parameter(self):
        self.validate_snippet(self.get_snippet_path("calls_parameter"))

    def test_lambda_parameter_call(self):
        self.validate_snippet(self.get_snippet_path("parameter_call"))

    def test_lambda_return_call(self):
        self.validate_snippet(self.get_snippet_path("return_call"))

    def test_chained_calls(self):
        self.validate_snippet(self.get_snippet_path("chained_calls"))
