from django.db import models
from django.db.models import Sum, Avg, Count, Q
from pathlib import Path
import yaml
from typing import Optional, TYPE_CHECKING
import re
from verifiers.models import Verifier
    


def clean_svcomp_i_file_further(code):
    # --- Phase 0: Pre-cleanup for malformed/stray code from previous cleanups ---
    # Remove stray 'else ; ... return __retres; }' blocks if they are unattached
    code = re.sub(r'^\s*else\s*;\s*__retres\s*=\s*\d+;\s*return_label:\s*return\s+__retres;\s*}\s*$', '', code, flags=re.MULTILINE)
    # Remove stray 'else ; tmp_0 = pthread_mutex_init...'
    code = re.sub(r'^\s*else\s*;\s*tmp_0\s*=\s*pthread_mutex_init.*?goto return_label;\s*.*?return_label:\s*return __retres;\s*}\s*$', '', code, flags=re.DOTALL | re.MULTILINE)
    # Remove stray 'else { ... return __retres; }'
    code = re.sub(r'^\s*else\s*{\s*__retres\s*=\s*-?\d+;\s*goto return_label;\s*}\s*return_label:\s*return __retres;\s*}\s*$', '', code, flags=re.DOTALL | re.MULTILINE)
    # Remove stray 'return;' lines, especially if they follow a declaration with attributes
    code = re.sub(r'__attribute__\s*\(\([^)]*\)\);\s*\n\s*return;', r'__attribute__ ((__nothrow__ , __leaf__)) __attribute__ ((__noreturn__));', code) # first restore if it was part of assert_fail
    code = re.sub(r'^\s*return;\s*$', '', code, flags=re.MULTILINE)
    # Remove stray 'unsigned' lines
    code = re.sub(r'^\s*unsigned\s*$', '', code, flags=re.MULTILINE)
    # Remove empty goto labels like ldv_xxxx: ;
    code = re.sub(r'\bldv_\d+:\s*;\s*\n', '', code)
    # Remove double semicolons ;;
    code = re.sub(r';\s*;', ';', code)


    # --- Phase 1: Remove Comment Headers & Frama-C specific (if any survived) ---
    # (Copied from previous, likely not needed if input is already cleaned once)
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    code = re.sub(r'// This file is part of the.*?SV-Benchmarks.*?\n(?:(?: |\t)*//.*?\n)*', '', code, flags=re.IGNORECASE)
    code = re.sub(r'(//|\*)\s*-?FileCopyrightText:.*?\n', '', code, flags=re.IGNORECASE)
    code = re.sub(r'(//|\*)\s*-?License-Identifier:.*?\n', '', code, flags=re.IGNORECASE)

    # --- Phase 2: Aggressively Remove Common Typedefs and Struct Declarations ---
    # Standard library types / large boilerplate structs often found in .i files
    struct_union_decl_patterns = [
        r'struct\s+_IO_FILE\s*;',
        r'typedef\s+struct\s+_IO_FILE\s+FILE\s*;',
        r'struct\s+_IO_marker\s*;',
        r'struct\s+_IO_codecvt\s*;',
        r'struct\s+_IO_wide_data\s*;',
        r'typedef\s+struct\s+__pthread_internal_list\s+__pthread_list_t\s*;',
        r'struct\s+_stdThread\s*;', # Declarations, not definitions
        r'struct\s+_stdThreadLock\s*;'
    ]
    for pattern in struct_union_decl_patterns:
        code = re.sub(pattern, '', code, flags=re.MULTILINE)

    # More general typedefs (if still present)
    typedef_patterns = [
        r'typedef\s+unsigned\s+long\s+size_t;',
        r'typedef\s+int\s+wchar_t;',
        r'typedef\s+(?:long|int)\s+\w+_t;', # e.g. time_t, int64_t
        r'typedef\s+unsigned\s+int\s+wint_t;',
    ]
    for pattern in typedef_patterns:
        code = re.sub(pattern, '', code, flags=re.MULTILINE)

    # --- Phase 3: Remove common helper/stub/LDV/VERIFIER functions & globals ---
    # Global constants (declarations and definitions)
    code = re.sub(r'(extern\s+)?int\s+const\s+GLOBAL_CONST_(?:TRUE|FALSE|FIVE)\s*(=\s*\d+)?;\n', '', code)

    # PrintLine function (declaration and definition)
    code = re.sub(r'void\s+printLine\s*\([^)]*\)\s*;\n', '', code)
    code = re.sub(r'void\s+printLine\s*\([^)]*\)\s*{.*?}\s*\n?', '', code, flags=re.DOTALL)

    # stdThread and ldv/verifier functions (definitions and declarations)
    # This will be more aggressive for LDV and VERIFIER functions
    stdthread_ldv_defs = [
        # stdThread functions (if any definitions remain)
        r'int\s+stdThreadCreate\s*\([^)]*\)\s*{.*?return __retres;\s*}\s*\n?',
        r'void\s+stdThreadLockDestroy\s*\([^)]*\)\s*{.*?return;\s*}\s*\n?',
        # LDV functions (more general removal of definitions)
        r'(?:static\s+)?(?:void|int|char\s*\*\s*|size_t|unsigned\s+long(?: long)?)\s+ldv_\w+\s*\([^)]*\)\s*{.*?}\s*\n?',
        # VERIFIER functions (definitions)
        r'(?:int|long|unsigned\s+int|unsigned\s+long(?: long)?)\s+__VERIFIER_nondet_\w+\s*\([^)]*\)\s*{.*?return.*?;.*?}\s*\n?',
    ]
    stdthread_ldv_decls = [
        # stdThread declarations
        r'int\s+stdThreadCreate\s*\([^)]*\);',
        r'void\s+stdThreadLockDestroy\s*\([^)]*\);', # Corrected based on your example.
        # LDV function declarations (more general)
        r'(?:extern\s+)?(?:void|int|char\s*\*\s*|size_t|unsigned\s+long(?: long)?)\s+ldv_\w+\s*\([^)]*\);',
        r'(?:extern\s+)?void\s+__assert_fail\s*\([^)]*\)(?:\s*__attribute__\s*\(\([^)]*\)\)\s*)*;', # with attributes
        r'(?:extern\s+)?void\s+reach_error\(\);', # if it survived
        r'(?:extern\s+)?void\s+assume_abort_if_not\(int\);', # if it survived
         # VERIFIER function declarations
        r'(?:extern\s+)?(?:int|long|unsigned\s+int|unsigned\s+long(?: long)?)\s+__VERIFIER_nondet_\w+\s*\([^)]*\);',
    ]

    for pattern in stdthread_ldv_defs: # Remove definitions first
        code = re.sub(pattern, '', code, flags=re.DOTALL)
    for pattern in stdthread_ldv_decls: # Then declarations
        code = re.sub(pattern, '', code)


    # --- Phase 4: Remove common external C library function declarations ---
    # List of common C lib function names
    c_lib_funcs = [
        "printf", "sscanf", "puts", "rand", "iswxdigit", "wprintf", "swscanf",
        "malloc", "free", "abort", "memcpy", "calloc", "memset", "time", "srand",
        "fgets", "atoi", "abs", "strcmp", "strncmp", "strlen", "memcmp", "memmove",
        "pthread_create", "pthread_exit", "pthread_join", "pthread_mutex_init",
        "pthread_mutex_destroy", "pthread_mutex_lock", "pthread_mutex_unlock"
    ]
    # Generic pattern for these declarations
    for func_name in c_lib_funcs:
        # Match "extern type func_name(...);" or "type func_name(...);"
        # Allows for simple types, pointer types, and "const"
        code = re.sub(r'(?:extern\s+)?(?:void|int|long|short|char|float|double|size_t|time_t|wint_t|FILE)\s*(?:\*\s*const|\*|\s+const)?\s*' + re.escape(func_name) + r'\s*\([^)]*\);', '', code)

    # Special cases for declarations that might be formatted differently
    code = re.sub(r'extern\s+unsigned short const\s*\*\*\s*__ctype_b_loc\(void\);', '', code)
    code = re.sub(r'extern\s+FILE\s+\*stdin\s*;', '', code) # More specific for stdin

    # --- Phase 5: Final Cleanup ---
    # Remove empty lines more aggressively
    code = re.sub(r'^\s*$\n', '', code, flags=re.MULTILINE)
    # Remove multiple blank newlines down to one
    code = re.sub(r'\n\n+', '\n', code)
    # Remove leading/trailing whitespace from the whole string
    code = code.strip()

    return code

def clean_i_file(code):
    # --- Phase 1: Remove Comment Headers & Frama-C specific ---
    # Remove block comments early, especially headers
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    # Remove SV-Benchmarks specific comment headers
    code = re.sub(r'// This file is part of the.*?SV-Benchmarks.*?\n(?:(?: |\t)*//.*?\n)*', '', code, flags=re.IGNORECASE)
    code = re.sub(r'(//|\*)\s*-?FileCopyrightText:.*?\n', '', code, flags=re.IGNORECASE)
    code = re.sub(r'(//|\*)\s*-?License-Identifier:.*?\n', '', code, flags=re.IGNORECASE)
    code = re.sub(r'/\*\s*Generated by Frama-C.*?\*/\s*\n?', '', code, flags=re.DOTALL) # If any survived or are different

    # --- Phase 2: Remove Common Typedefs and Structs (often from system headers) ---
    # Standard library types / large boilerplate structs often found in .i files
    # Order matters: remove definitions then typedefs that might use them.
    struct_union_patterns = [
        r'struct\s+_IO_FILE\s*{.*?};',
        r'struct\s+_IO_marker\s*{.*?};',
        r'struct\s+_IO_codecvt\s*{.*?};',
        r'struct\s+_IO_wide_data\s*{.*?};',
        r'struct\s+__pthread_internal_list\s*{.*?};',
        r'struct\s+__pthread_mutex_s\s*{.*?};',
        r'union\s+__anonunion_pthread_mutexattr_t_\d+\s*{.*?};', # Handle varying numbers
        r'union\s+pthread_attr_t\s*{.*?};',
        r'union\s+__anonunion_pthread_mutex_t_\d+\s*{.*?};',
        # Specific to your example's _stdThread and _stdThreadLock
        r'struct\s+_stdThread\s*{.*?};',
        r'struct\s+_stdThreadLock\s*{.*?};',
    ]
    for pattern in struct_union_patterns:
        code = re.sub(pattern, '', code, flags=re.DOTALL | re.MULTILINE)

    typedef_patterns = [
        r'typedef\s+unsigned\s+long\s+size_t;',
        r'typedef\s+int\s+wchar_t;',
        r'typedef\s+long\s+__int64_t;',
        r'typedef\s+__int64_t\s+int64_t;',
        r'typedef\s+unsigned\s+int\s+wint_t;',
        r'typedef\s+struct\s+_twoIntsStruct\s+twoIntsStruct;', # From your example
        r'typedef\s+long\s+__off_t;',
        r'typedef\s+long\s+__off64_t;',
        r'typedef\s+long\s+__time_t;',
        r'typedef\s+__time_t\s+time_t;',
        r'typedef\s+void\s+_IO_lock_t;',
        r'typedef\s+struct\s+_IO_FILE\s+_IO_FILE;', # Common typedef for the struct
        r'typedef\s+unsigned\s+long\s+pthread_t;',
        r'typedef\s+union\s+__anonunion_pthread_mutexattr_t_\d+\s+pthread_mutexattr_t;',
        r'typedef\s+union\s+pthread_attr_t\s+pthread_attr_t;',
        r'typedef\s+union\s+__anonunion_pthread_mutex_t_\d+\s+pthread_mutex_t;',
        # Specific to your example's stdThread
        r'typedef\s+struct\s+_stdThread\s*\*stdThread;',
        r'typedef\s+struct\s+_stdThreadLock\s*\*stdThreadLock;',
        # General catch for simple typedefs (non-struct/union) if missed
        r'typedef\s+(?:unsigned\s+)?(?:long\s+long|long|int|short|char|double|float|void)\s+\w+(?:_t)?\s*;',
        # Empty/forward struct/union declarations that are then typedef'd (or not used)
        r'typedef\s+struct\s+\w+\s*;', # e.g. typedef struct _someStruct someStruct_t; (if _someStruct is removed)
    ]
    for pattern in typedef_patterns:
        code = re.sub(pattern, '', code, flags=re.MULTILINE)

    # Remove struct _twoIntsStruct { ... }; (definition, if typedef already handled or it's standalone)
    code = re.sub(r'struct\s+_twoIntsStruct\s*{[^}]*};', '', code, flags=re.DOTALL)
    # Remove dangling struct/typedef struct declarations:
    code = re.sub(r'^\s*struct\s*;\s*$', '', code, flags=re.MULTILINE)
    code = re.sub(r'^\s*typedef\s+struct\s*;\s*$', '', code, flags=re.MULTILINE)


    # --- Phase 3: Remove common helper/stub/LDV/VERIFIER functions & globals ---
    # Stub functions like good1(), bad1()
    code = re.sub(r'void\s+(good|bad)\d+\s*\([^)]*\)\s*{\s*(?:return;)?\s*}\s*\n?', '', code)

    # Redundant global variables (declarations and definitions)
    code = re.sub(r'(extern\s+)?int\s+global(True|False|Five)\s*(=\s*\d+)?;\n', '', code)
    code = re.sub(r'(extern\s+)?int\s+const\s*(=\s*\d+)?;\n', '', code) # Matches "int const;" and "int const = value;"
    code = re.sub(r'(extern\s+)?int\s+globalArgc\s*(=\s*0)?;\n', '', code)
    code = re.sub(r'(extern\s+)?char\s*\*\*\s*globalArgv\s*(=\s*\(char\s*\*\*\)0)?;\n', '', code)


    # Print and other utility functions (declarations and definitions)
    # Covers printXYZLine, decodeHexChars, globalReturnsXYZ
    util_func_patterns_defs = [
        r'void\s+print\w+Line\s*\([^)]*\)\s*{.*?}\s*\n?',
        r'size_t\s+decodeHex(?:W)?Chars\s*\([^)]*\)\s*{.*?return\s+numWritten;\s*}\s*\n?',
        r'int\s+globalReturns(True|False|TrueOrFalse)\s*\([^)]*\)\s*{.*?return.*?;\s*}\s*\n?'
    ]
    util_func_patterns_decls = [
        r'void\s+print\w+Line\s*\([^)]*\);',
        r'size_t\s+decodeHex(?:W)?Chars\s*\([^)]*\);',
        r'int\s+globalReturns(?:True|False|TrueOrFalse)\s*\([^)]*\);'
    ]
    for pattern in util_func_patterns_defs: # Remove definitions first
        code = re.sub(pattern, '', code, flags=re.DOTALL)
    for pattern in util_func_patterns_decls: # Then declarations
        code = re.sub(pattern, '', code)

    # stdThread and ldv/verifier functions (common in SV-COMP)
    stdthread_ldv_defs = [
        r'(?:static\s+)?void\s*\*\s*internal_start\s*\([^)]*\)\s*{.*?pthread_exit\(.*?\);\s*.*?}\s*\n?',
        r'int\s+stdThread(?:Create|Join|Destroy)\s*\([^)]*\)\s*{.*?return.*?;.*?}\s*\n?',
        r'int\s+stdThreadLock(?:Create|Destroy)\s*\([^)]*\)\s*{.*?return.*?;.*?}\s*\n?',
        r'void\s+stdThreadLock(?:Acquire|Release)\s*\([^)]*\)\s*{.*?return;\s*}\s*\n?',
        r'(?:void|int|char\s*\*\s*|size_t)\s+ldv_\w+\s*\([^)]*\)\s*{.*?}\s*\n?', # Basic ldv functions
        r'void\s+reach_error\(\)\s*{.*?}\s*\n?',
        r'void\s+assume_abort_if_not\s*\(int cond\)\s*{.*?}\s*\n?',
        r'(?:int|long|unsigned\s+int|unsigned\s+long(?: long)?)\s+__VERIFIER_nondet_\w+\s*\([^)]*\)\s*{.*?return.*?;.*?}\s*\n?',
    ]
    stdthread_ldv_decls = [
        r'int\s+stdThread(?:Create|Join|Destroy)\s*\([^)]*\);',
        r'int\s+stdThreadLockCreate\s*\([^)]*\);',
        r'void\s+stdThreadLock(?:Acquire|Release|Destroy)\s*\([^)]*\);',
        r'(?:extern\s+)?(?:void|int|char\s*\*\s*|size_t)\s+ldv_\w+\s*\([^)]*\);',
        r'(?:extern\s+)?void\s+reach_error\(\);',
        r'(?:extern\s+)?void\s+assume_abort_if_not\(int\);', # if prototype uses 'int' instead of 'int cond'
        r'(?:extern\s+)?void\s+__assert_fail\s*\([^)]*\);',
        r'(?:extern\s+)?(int|long|unsigned\s+int|unsigned\s+long(?: long)?)\s+__VERIFIER_nondet_\w+\s*\([^)]*\);',
    ]

    for pattern in stdthread_ldv_defs:
        code = re.sub(pattern, '', code, flags=re.DOTALL)
    for pattern in stdthread_ldv_decls:
        code = re.sub(pattern, '', code)


    # --- Phase 4: Remove common external declarations ---
    extern_decls = [
        r'extern\s+struct\s+_IO_FILE\s+\*(?:stdin|stdout|stderr);',
        r'extern\s+\*stdin;\s*\n', # from your example
        r'extern\s+unsigned short const\s*\*\*\s*__ctype_b_loc\(void\);',
        # Common C library functions
        r'extern\s+(?:int|void|char\s*\*|size_t|time_t)\s+(?:printf|puts|sscanf|rand|iswxdigit|wprintf|swscanf|atoi|abs|strcmp|strncmp|strlen|memcmp|memset|memcpy|memmove|fgets|srand|free|exit|abort|pthread_exit|malloc|calloc|realloc|time|pthread_create|pthread_join|pthread_mutex_init|pthread_mutex_destroy|pthread_mutex_lock|pthread_mutex_unlock)\s*\([^)]*\);'
    ]
    # A more specific version of the original one for common stdlib functions:
    code = re.sub(r'(?:extern\s+)?(char\s+\*fgets|int\s+atoi|void\s+srand|time_t\s+time)\s*\([^)]*\);', '', code)

    for pattern in extern_decls:
        code = re.sub(pattern, '', code)

    # --- Phase 5: Final Cleanup ---
    # Remove multiple blank lines
    code = re.sub(r'\n\s*\n+', '\n\n', code)
    # Remove lines that are now empty or contain only whitespace
    code = "\n".join([line for line in code.splitlines() if line.strip()])

    return clean_svcomp_i_file_further(code)


class VerificationCategory(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def best_verifier(self) -> Optional["Verifier"]:
        best_verifier_data = self.verifier_ranking()
        if len(best_verifier_data) == 0:
            return None
        best_verifier_data = best_verifier_data[0]  # Get the top verifier
        return Verifier.objects.get(name=best_verifier_data['verifier__name']) if best_verifier_data else None
        
    def verifier_task_summary(self, verifier_name):
        """Get summary of a specific verifier's performance grouped by verification task"""
        from benchmarks.models import Benchmark
        
        task_summary = (
            Benchmark.objects
            .filter(verification_task__category=self, verifier__name=verifier_name)
            .values('verification_task__id')
            .annotate(
                count=Count('id'),
                avg_score=Avg('raw_score'),
                sum_score=Sum('raw_score'),
                avg_cpu=Avg('cpu'),
                avg_memory=Avg('memory'),
                correct_count=Count('id', filter=Q(is_correct=True)),
                total_benchmarks=Count('id'), 
                verifier__name=models.F('verifier__name'),
            )
        )
        
        return task_summary

    def verifier_ranking(self):
        """Get summary of all verifiers' performance grouped by verification task"""
        from benchmarks.models import Benchmark
        results = []
        for v in Verifier.objects.all():
            if not Benchmark.objects.filter(verification_task__category=self, verifier=v).exists():
                continue
            verifier_task_summary = self.verifier_task_summary(v.name)
            aggregated_summary = verifier_task_summary.aggregate(
                total_benchmarks=Sum('count'),
                sum_of_avg_scores=Sum('avg_score'),  # Sum of all average scores per task
                total_sum_score=Sum('sum_score'),
                avg_cpu_across_tasks=Avg('avg_cpu'),
                avg_memory_across_tasks=Avg('avg_memory'),
                total_correct_count=Sum('correct_count'),
                task_count=Count('verification_task__id'),
            )
            aggregated_summary['verifier__name'] = v.name
            aggregated_summary["vts_covered"] = verifier_task_summary.count()
            aggregated_summary["correct_accuracy"] = aggregated_summary['total_correct_count'] / aggregated_summary['total_benchmarks'] if aggregated_summary['total_benchmarks'] > 0 else 0
            aggregated_summary["avg_score_per_benchmark"] = aggregated_summary['sum_of_avg_scores'] / aggregated_summary['vts_covered'] if aggregated_summary['total_benchmarks'] > 0 else 0
            results.append(aggregated_summary)

        results = sorted(results, key=lambda x: x['sum_of_avg_scores'], reverse=True)
        return results

class VerificationSubcategory(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(VerificationCategory, on_delete=models.CASCADE, related_name='subcategories')

    def __str__(self):
        return f"{self.name} ({self.category.name})"

class VerificationSet(models.Model):
    name = models.CharField(max_length=255)
    subcategories = models.ManyToManyField(VerificationSubcategory, blank=True)
    patterns = models.TextField(
        help_text="Patterns to match verification tasks in this subcategory. Use regex-like syntax with '*' for wildcards.", 
        default=""
    )

    def __str__(self):
        return f"{self.name}"

class Status(models.TextChoices):
    TRUE = "true", "True"
    FALSE = "false", "False"
    INVALID_TASK = "invalid_task", "Invalid Task"
    UNKNOWN = "unknown", "Unknown"
    ERROR = "error", "Error"

class VerificationTask(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(VerificationCategory, on_delete=models.CASCADE)
    expected_result = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.TRUE,
        help_text="Expected result for the task."
    )
    subcategories = models.ManyToManyField(
        VerificationSubcategory,
        blank=True,
        help_text="Subcategories of the verification task."
    )

    class Meta:
        ordering = ['category', "name"]

    def __str__(self):
        return self.name
    
    @property
    def yml_file_path(self) -> Path:
        return Path("sv-benchmarks/c") / self.name[:self.name.find("yml")+3]
    
    def get_yml_config(self):
        try:
            with open(self.yml_file_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            return None
        
    def get_c_file_path(self) -> Path:
        return self.yml_file_path.parent / Path(self.get_yml_config().get("input_files")).with_suffix(".c")
    
    def get_i_file_path(self) -> Path:
        return self.yml_file_path.parent / Path(self.get_yml_config().get("input_files")).with_suffix(".i")

    def read_c_file(self) -> str | None:
        c_file_path = self.get_c_file_path()
        if c_file_path.exists():
            with open(c_file_path, 'r') as file:
                return file.read()
        return None
    
    def read_i_file(self) -> str | None:
        c_file_path = self.get_i_file_path()
        if c_file_path.exists():
            with open(c_file_path, 'r') as file:
                return clean_i_file(file.read())
        return None
    
    @classmethod
    def extract_expected_result(cls, name: str) -> str:
        name = name.replace("(valid-deref)", "")
        name = name.replace("(valid-memtrack)", "")
        name = name.replace("(valid-free)", "")
        if name.endswith("true"):
            return Status.TRUE
        elif name.endswith("false"):
            return Status.FALSE
        else:
            return Status.INVALID_TASK
        
    def has_c_file(self) -> bool:
        return self.get_c_file_path().exists()
    
    def has_i_file(self) -> bool:
        return self.get_i_file_path().exists()
    