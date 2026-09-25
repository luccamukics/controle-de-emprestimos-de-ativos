import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from caminhos import pasta_aplicacao


class TestCaminhos(unittest.TestCase):
    def test_codigo_python_usa_raiz_do_projeto(self):
        self.assertEqual(pasta_aplicacao(), Path(__file__).resolve().parent.parent)

    def test_executavel_usa_pasta_ao_lado_do_exe(self):
        with patch.object(sys, "frozen", True, create=True), patch.object(
            sys, "executable", r"C:\Programas\ControleEmprestimos\ControleEmprestimos.exe"
        ):
            self.assertEqual(
                pasta_aplicacao(), Path(sys.executable).resolve().parent
            )


if __name__ == "__main__":
    unittest.main()
