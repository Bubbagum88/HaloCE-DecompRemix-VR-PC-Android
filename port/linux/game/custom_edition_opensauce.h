/*
CUSTOM_EDITION_OPENSAUCE.H

OpenSauce script functions Custom Edition campaigns call
(custom_edition_opensauce.c). The script engine finds them past its own
table and GulchCE's MCC functions (hs.c, hs_runtime.c).
*/

#ifndef __CUSTOM_EDITION_OPENSAUCE_H
#define __CUSTOM_EDITION_OPENSAUCE_H

/* the first index (GulchCE's MCC functions are 0x7000-0x70FF) */
#define CUSTOM_EDITION_HS_FIRST 0x7100

struct hs_function_definition;
struct hs_syntax_node;
struct data_array;

/* the function of index `function_index`, or NULL when it is none of these */
struct hs_function_definition *custom_edition_script_function(
	short function_index);
/* the index of the function named `name`, or NONE */
short custom_edition_script_find(
	char const *name);
/* whether `call` calls one of these with arguments of the types it takes */
boolean custom_edition_script_call_valid(
	struct hs_syntax_node const *call,
	struct data_array *syntax);

#endif
