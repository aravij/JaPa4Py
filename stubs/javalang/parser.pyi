from . import tree as tree, util as util
from .tokenizer import (
    Annotation as Annotation,
    BasicType as BasicType,
    EndOfInput as EndOfInput,
    Identifier as Identifier,
    JavaToken as JavaToken,
    Keyword as Keyword,
    Literal as Literal,
    Modifier as Modifier,
    Operator as Operator,
)
from typing import Any, Optional

ENABLE_DEBUG_SUPPORT: bool

def parse_debug(method: Any): ...

class JavaParserBaseException(Exception):
    def __init__(self, message: str = ...) -> None: ...

class JavaSyntaxError(JavaParserBaseException):
    description: Any = ...
    at: Any = ...
    def __init__(self, description: Any, at: Optional[Any] = ...) -> None: ...

class JavaParserError(JavaParserBaseException): ...

class Parser:
    operator_precedence: Any = ...
    tokens: Any = ...
    debug: bool = ...
    def __init__(self, tokens: Any) -> None: ...
    def set_debug(self, debug: bool = ...) -> None: ...
    def parse(self): ...
    def illegal(self, description: Any, at: Optional[Any] = ...) -> None: ...
    def accept(self, *accepts: Any): ...
    def would_accept(self, *accepts: Any): ...
    def try_accept(self, *accepts: Any): ...
    def build_binary_operation(self, parts: Any, start_level: int = ...): ...
    def is_annotation(self, i: int = ...): ...
    def is_annotation_declaration(self, i: int = ...): ...
    def parse_identifier(self): ...
    def parse_qualified_identifier(self): ...
    def parse_qualified_identifier_list(self): ...
    def parse_compilation_unit(self): ...
    def parse_import_declaration(self): ...
    def parse_type_declaration(self): ...
    def parse_class_or_interface_declaration(self): ...
    def parse_normal_class_declaration(self): ...
    def parse_enum_declaration(self): ...
    def parse_normal_interface_declaration(self): ...
    def parse_annotation_type_declaration(self): ...
    def parse_type(self): ...
    def parse_basic_type(self): ...
    def parse_reference_type(self): ...
    def parse_type_arguments(self): ...
    def parse_type_argument(self): ...
    def parse_nonwildcard_type_arguments(self): ...
    def parse_type_list(self): ...
    def parse_type_arguments_or_diamond(self): ...
    def parse_nonwildcard_type_arguments_or_diamond(self): ...
    def parse_type_parameters(self): ...
    def parse_type_parameter(self): ...
    def parse_array_dimension(self): ...
    def parse_modifiers(self): ...
    def parse_annotations(self): ...
    def parse_annotation(self): ...
    def parse_annotation_element(self): ...
    def parse_element_value_pairs(self): ...
    def parse_element_value_pair(self): ...
    def parse_element_value(self): ...
    def parse_element_value_array_initializer(self): ...
    def parse_element_values(self): ...
    def parse_class_body(self): ...
    def parse_class_body_declaration(self): ...
    def parse_member_declaration(self): ...
    def parse_method_or_field_declaraction(self): ...
    def parse_method_or_field_rest(self): ...
    def parse_field_declarators_rest(self): ...
    def parse_method_declarator_rest(self): ...
    def parse_void_method_declarator_rest(self): ...
    def parse_constructor_declarator_rest(self): ...
    def parse_generic_method_or_constructor_declaration(self): ...
    def parse_interface_body(self): ...
    def parse_interface_body_declaration(self): ...
    def parse_interface_member_declaration(self): ...
    def parse_interface_method_or_field_declaration(self): ...
    def parse_interface_method_or_field_rest(self): ...
    def parse_constant_declarators_rest(self): ...
    def parse_constant_declarator_rest(self): ...
    def parse_constant_declarator(self): ...
    def parse_interface_method_declarator_rest(self): ...
    def parse_void_interface_method_declarator_rest(self): ...
    def parse_interface_generic_method_declarator(self): ...
    def parse_formal_parameters(self): ...
    def parse_variable_modifiers(self): ...
    def parse_variable_declators(self): ...
    def parse_variable_declarators(self): ...
    def parse_variable_declarator(self): ...
    def parse_variable_declarator_rest(self): ...
    def parse_variable_initializer(self): ...
    def parse_array_initializer(self): ...
    def parse_block(self): ...
    def parse_block_statement(self): ...
    def parse_local_variable_declaration_statement(self): ...
    def parse_statement(self): ...
    def parse_catches(self): ...
    def parse_catch_clause(self): ...
    def parse_resource_specification(self): ...
    def parse_resource(self): ...
    def parse_switch_block_statement_groups(self): ...
    def parse_switch_block_statement_group(self): ...
    def parse_for_control(self): ...
    def parse_for_var_control(self): ...
    def parse_for_var_control_rest(self): ...
    def parse_for_variable_declarator_rest(self): ...
    def parse_for_init_or_update(self): ...
    def parse_expression(self): ...
    def parse_expressionl(self): ...
    def parse_expression_2(self): ...
    def parse_expression_2_rest(self): ...
    def parse_expression_3(self): ...
    def parse_method_reference(self): ...
    def parse_lambda_expression(self): ...
    def parse_lambda_method_body(self): ...
    def parse_infix_operator(self): ...
    def parse_primary(self): ...
    def parse_literal(self): ...
    def parse_par_expression(self): ...
    def parse_arguments(self): ...
    def parse_super_suffix(self): ...
    def parse_explicit_generic_invocation_suffix(self): ...
    def parse_creator(self): ...
    def parse_created_name(self): ...
    def parse_class_creator_rest(self): ...
    def parse_array_creator_rest(self): ...
    def parse_identifier_suffix(self): ...
    def parse_explicit_generic_invocation(self): ...
    def parse_inner_creator(self): ...
    def parse_selector(self): ...
    def parse_enum_body(self): ...
    def parse_enum_constant(self): ...
    def parse_annotation_type_body(self): ...
    def parse_annotation_type_element_declarations(self): ...
    def parse_annotation_type_element_declaration(self): ...
    def parse_annotation_method_or_constant_rest(self): ...

def parse(tokens: Any, debug: bool = ...): ...
