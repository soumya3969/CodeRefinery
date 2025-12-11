"""
Test utilities module.
"""
import pytest
from coderefinery.utils import (
    extract_functions, extract_classes, extract_imports,
    get_code_metrics, validate_python_syntax, suggest_refactoring,
    calculate_maintainability_index
)


def test_extract_functions():
    """Test function extraction."""
    code = """
def simple_func():
    pass

async def async_func(param1, param2):
    '''Async function with parameters.'''
    return param1 + param2

def func_with_docstring():
    '''This function has a docstring.'''
    return True
"""
    
    functions = extract_functions(code)
    assert len(functions) == 3
    
    # Check simple function
    simple = next(f for f in functions if f['name'] == 'simple_func')
    assert simple['args'] == []
    assert not simple['is_async']
    
    # Check async function
    async_f = next(f for f in functions if f['name'] == 'async_func')
    assert async_f['args'] == ['param1', 'param2']
    assert async_f['is_async']
    
    # Check function with docstring
    with_doc = next(f for f in functions if f['name'] == 'func_with_docstring')
    assert with_doc['docstring'] is not None


def test_extract_classes():
    """Test class extraction."""
    code = """
class SimpleClass:
    pass

class ComplexClass(BaseClass):
    '''A complex class.'''
    
    def method1(self):
        pass
    
    async def async_method(self):
        pass
"""
    
    classes = extract_classes(code)
    assert len(classes) == 2
    
    # Check simple class
    simple = next(c for c in classes if c['name'] == 'SimpleClass')
    assert len(simple['methods']) == 0
    
    # Check complex class
    complex_c = next(c for c in classes if c['name'] == 'ComplexClass')
    assert len(complex_c['methods']) == 2
    assert complex_c['docstring'] is not None


def test_extract_imports():
    """Test import extraction."""
    code = """
import os
import sys as system
from pathlib import Path
from collections import defaultdict, Counter
from .local import helper
"""
    
    imports = extract_imports(code)
    
    # Check regular imports
    assert len(imports['imports']) == 2
    os_import = next(i for i in imports['imports'] if i['module'] == 'os')
    assert os_import['alias'] is None
    
    sys_import = next(i for i in imports['imports'] if i['module'] == 'sys')
    assert sys_import['alias'] == 'system'
    
    # Check from imports
    assert len(imports['from_imports']) == 4
    path_import = next(i for i in imports['from_imports'] if i['name'] == 'Path')
    assert path_import['module'] == 'pathlib'


def test_get_code_metrics():
    """Test code metrics calculation."""
    code = """
# This is a comment
import os

def function():
    '''Docstring'''
    return True

# Another comment
x = 42
"""
    
    metrics = get_code_metrics(code)
    
    assert metrics['total_lines'] == 9
    assert metrics['comment_lines'] == 2
    assert metrics['blank_lines'] >= 1
    assert metrics['code_lines'] > 0
    assert 0 <= metrics['code_percentage'] <= 100


def test_validate_python_syntax():
    """Test Python syntax validation."""
    # Valid syntax
    valid_code = "def test(): return True"
    is_valid, error = validate_python_syntax(valid_code)
    assert is_valid
    assert error is None
    
    # Invalid syntax
    invalid_code = "def test( return True"
    is_valid, error = validate_python_syntax(invalid_code)
    assert not is_valid
    assert error is not None


def test_suggest_refactoring():
    """Test refactoring suggestions."""
    code = """
def function_with_many_params(a, b, c, d, e, f, g):
    return a + b + c + d + e + f + g

def function_without_docstring():
    return True

class ClassWithoutDocstring:
    def method1(self): pass
    def method2(self): pass
"""
    
    suggestions = suggest_refactoring(code)
    
    # Should suggest parameter reduction
    param_suggestions = [s for s in suggestions if s['type'] == 'parameter_list']
    assert len(param_suggestions) > 0
    
    # Should suggest adding docstrings
    doc_suggestions = [s for s in suggestions if s['type'] == 'documentation']
    assert len(doc_suggestions) >= 2  # Function and class


def test_calculate_maintainability_index():
    """Test maintainability index calculation."""
    # Simple, well-structured code
    good_code = """
def well_documented_function():
    '''This function is well documented.'''
    return True

class WellStructuredClass:
    '''A well-structured class.'''
    
    def method(self):
        '''A method with documentation.'''
        pass
"""
    
    index = calculate_maintainability_index(good_code)
    assert 0 <= index <= 100
    
    # Should be reasonably high for good code
    assert index > 50
    
    # Empty code
    empty_index = calculate_maintainability_index("")
    assert empty_index == 100.0


def test_extract_functions_with_syntax_error():
    """Test function extraction with syntax errors."""
    invalid_code = "def broken_func( print('test')"
    functions = extract_functions(invalid_code)
    assert len(functions) == 0


def test_extract_classes_with_syntax_error():
    """Test class extraction with syntax errors."""
    invalid_code = "class BrokenClass print('test')"
    classes = extract_classes(invalid_code)
    assert len(classes) == 0


def test_complex_imports():
    """Test complex import scenarios."""
    code = """
from package.subpackage import (
    module1,
    module2 as mod2
)
from ..parent import sibling
import package.deeply.nested.module
"""
    
    imports = extract_imports(code)
    
    # Should handle multiline imports
    assert len(imports['from_imports']) >= 3
    
    # Check relative import
    relative_import = next((i for i in imports['from_imports'] 
                           if i['module'] == '..parent'), None)
    assert relative_import is not None
    assert relative_import['level'] == 2


@pytest.mark.parametrize("code,expected_functions", [
    ("", 0),
    ("x = 42", 0),
    ("def f(): pass", 1),
    ("def f(): pass\ndef g(): pass", 2),
    ("class C:\n    def m(self): pass", 1),
])
def test_function_extraction_parametrized(code, expected_functions):
    """Parametrized test for function extraction."""
    functions = extract_functions(code)
    assert len(functions) == expected_functions